import AppKit
import Combine
import Foundation
import ServiceManagement
import SwiftUI

@MainActor
final class AppController: ObservableObject {

    let mottoStore = MottoStore()
    private let state = GenerationState()
    private let finder = FinderWatcher()

    private var editorWindow: NSWindow?

    init() {
        SettingsMigration.runIfNeeded()
        syncLoginItemWithDefaults()

        finder.start { [weak self] in
            Task { @MainActor [weak self] in
                await self?.runGeneration(source: .auto)
            }
        }
    }

    func showEditorWindow() {
        NSApp.setActivationPolicy(.accessory)
        if let w = editorWindow, w.isVisible {
            w.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            return
        }

        let view = MottoEditorView(
            store: mottoStore,
            onRefresh: { [weak self] in self?.refreshWallpaper() },
            onQuit: { [weak self] in self?.quit() },
            onAutostartChange: { [weak self] enabled in
                self?.applyLoginItem(enabled: enabled)
            }
        )
        let hosting = NSHostingController(rootView: view)
        hosting.view.frame = NSRect(x: 0, y: 0, width: 460, height: 520)

        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 460, height: 520),
            styleMask: [.titled, .closable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.contentViewController = hosting
        window.title = "SlapPaper"
        window.contentMinSize = NSSize(width: 460, height: 400)
        window.center()
        window.isReleasedWhenClosed = false
        editorWindow = window

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func refreshWallpaper() {
        Task {
            await runGeneration(source: .manual)
        }
    }

    func quit() {
        finder.stop()
        NSApp.terminate(nil)
    }

    func applyLoginItem(enabled: Bool) {
        UserDefaults.standard.set(enabled, forKey: "autostart")
        do {
            if enabled {
                try SMAppService.mainApp.register()
            } else {
                try SMAppService.mainApp.unregister()
            }
        } catch {
            AppLog.append("Login item register/unregister failed: \(error.localizedDescription)")
        }
    }

    private func syncLoginItemWithDefaults() {
        guard UserDefaults.standard.bool(forKey: "autostart") else { return }
        do {
            try SMAppService.mainApp.register()
        } catch {
            AppLog.append("Login item sync on launch failed: \(error.localizedDescription)")
        }
    }

    private func runGeneration(source: GenerationState.Source) async {
        let allowed = await state.beginGeneration(source: source)
        guard allowed else { return }

        let mottos = mottoStore.runtimeMottos()
        let dims = WallpaperGenerator.targetDimensions()
        let st = state

        await Task.detached(priority: .userInitiated) {
            do {
                _ = try WallpaperGenerator().generate(usingMottos: mottos, dimensions: dims)
            } catch {
                AppLog.append("\(source.rawValue) generation failed: \(error.localizedDescription)")
            }
            await st.finishGeneration()
        }.value
    }
}
