from slappaper.config import FINDER_BUNDLE_ID

try:
    import AppKit
except Exception:
    AppKit = None


APPLICATION_KEY = (
    AppKit.NSWorkspaceApplicationKey if AppKit is not None else "NSWorkspaceApplicationKey"
)
ACTIVATION_NOTIFICATION = (
    AppKit.NSWorkspaceDidActivateApplicationNotification
    if AppKit is not None
    else "NSWorkspaceDidActivateApplicationNotification"
)


class FinderActivationListener:
    def __init__(self, on_finder_activated, notification_center=None, logger=None):
        self._on_finder_activated = on_finder_activated
        self._notification_center = notification_center
        self._logger = logger or (lambda message: None)
        self._observer = None

    def start(self):
        if self._observer is not None:
            return

        if self._notification_center is None:
            if AppKit is None:
                raise RuntimeError("NSWorkspace is unavailable on this platform.")
            self._notification_center = AppKit.NSWorkspace.sharedWorkspace().notificationCenter()

        self._observer = self._notification_center.addObserverForName_object_queue_usingBlock_(
            ACTIVATION_NOTIFICATION,
            None,
            None,
            self._handle_notification,
        )

    def stop(self):
        if self._observer is None or self._notification_center is None:
            return
        self._notification_center.removeObserver_(self._observer)
        self._observer = None

    def _handle_notification(self, notification):
        try:
            user_info_getter = getattr(notification, "userInfo", None)
            if callable(user_info_getter):
                user_info = user_info_getter() or {}
            else:
                user_info = user_info_getter or {}

            application = user_info.get(APPLICATION_KEY)
            if application is None:
                return

            bundle_id_getter = getattr(application, "bundleIdentifier", None)
            bundle_id = bundle_id_getter() if callable(bundle_id_getter) else bundle_id_getter
            if bundle_id == FINDER_BUNDLE_ID:
                self._on_finder_activated()
        except Exception as exc:
            self._logger(f"Finder activation listener error: {exc}")
