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
            guard Self.isFinderActivation(notification.userInfo) else { return }
            onFinderActivated()
        }
    }

    func stop() {
        if let obs = observation {
            notificationCenter.removeObserver(obs)
            observation = nil
        }
    }

    static func isFinderActivation(_ userInfo: [AnyHashable: Any]?) -> Bool {
        guard let app = userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication else {
            return false
        }
        return app.bundleIdentifier == Constants.finderBundleID
    }
}
