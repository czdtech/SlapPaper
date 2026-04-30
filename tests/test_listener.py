import importlib
import types
import unittest


def load_listener_module():
    return importlib.import_module("slappaper.listener")


class FakeNotificationCenter:
    def __init__(self):
        self.observer = None
        self.removed = None

    def addObserverForName_object_queue_usingBlock_(self, name, obj, queue, callback):
        self.observer = callback
        self.name = name
        return "observer-token"

    def removeObserver_(self, observer):
        self.removed = observer


class FinderActivationListenerTests(unittest.TestCase):
    def setUp(self):
        self.listener_module = load_listener_module()

    def test_start_registers_notification_handler(self):
        center = FakeNotificationCenter()
        events = []
        listener = self.listener_module.FinderActivationListener(
            notification_center=center,
            on_finder_activated=lambda: events.append("finder"),
        )

        listener.start()
        listener.stop()

        self.assertEqual(center.removed, "observer-token")
        self.assertEqual(events, [])

    def test_only_finder_bundle_id_triggers_callback(self):
        center = FakeNotificationCenter()
        events = []
        listener = self.listener_module.FinderActivationListener(
            notification_center=center,
            on_finder_activated=lambda: events.append("finder"),
        )
        listener.start()

        non_finder_app = types.SimpleNamespace(bundleIdentifier=lambda: "com.microsoft.VSCode")
        finder_app = types.SimpleNamespace(bundleIdentifier=lambda: "com.apple.finder")

        center.observer(types.SimpleNamespace(userInfo=lambda: {self.listener_module.APPLICATION_KEY: non_finder_app}))
        center.observer(types.SimpleNamespace(userInfo=lambda: {self.listener_module.APPLICATION_KEY: finder_app}))

        self.assertEqual(events, ["finder"])


if __name__ == "__main__":
    unittest.main()
