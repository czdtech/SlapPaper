import AppKit
import SwiftUI

private final class AppActivationDelegate: NSObject, NSApplicationDelegate {
    func applicationWillFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
    }
}

@main
struct SlapPaperApp: App {
    @StateObject private var controller = AppController()
    @NSApplicationDelegateAdaptor(AppActivationDelegate.self) private var activationDelegate

    var body: some Scene {
        MenuBarExtra("SlapPaper", systemImage: "text.quote") {
            Button("文案库…") {
                controller.showEditorWindow()
            }
            Button("刷新壁纸") {
                controller.refreshWallpaper()
            }
            Divider()
            Button("退出") {
                controller.quit()
            }
        }
    }
}
