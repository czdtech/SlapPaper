import AppKit
import Foundation

final class FinderWatcher {
    private var observation: NSObjectProtocol?
    private let notificationCenter: NotificationCenter

    init(notificationCenter: NotificationCenter = NSWorkspace.shared.notificationCenter) {
        self.notificationCenter = notificationCenter
    }

    func start(onFinderActivated: @escaping () -> Void) {
        stop()
        observation = notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification,
            object: nil,
            queue: .main
        ) { notification in
            guard
                let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication,
                app.bundleIdentifier == Constants.finderBundleID
            else { return }
            onFinderActivated()
        }
    }

    func stop() {
        if let obs = observation {
            notificationCenter.removeObserver(obs)
            observation = nil
        }
    }
}
