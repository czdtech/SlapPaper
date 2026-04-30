import importlib
import unittest
from unittest import mock


def load_app_module():
    return importlib.import_module("slappaper.app")


class InlineThread:
    def __init__(self, target=None, daemon=None):
        self.target = target
        self.daemon = daemon

    def start(self):
        if self.target is not None:
            self.target()


class SlapPaperAppTests(unittest.TestCase):
    def setUp(self):
        self.app_module = load_app_module()

    def test_finder_event_uses_auto_generation_path(self):
        state = mock.Mock()
        state.begin_generation.side_effect = [True]
        state.finish_generation.return_value = None
        generator = mock.Mock()
        app = self.app_module.SlapPaperApp(
            generator=generator,
            state=state,
            listener=mock.Mock(),
            store=mock.Mock(),
            settings_store=mock.Mock(),
            thread_factory=InlineThread,
        )

        app.handle_finder_activated()

        state.begin_generation.assert_called_once_with("auto")
        generator.generate.assert_called_once()

    def test_manual_refresh_bypasses_auto_debounce_path(self):
        state = mock.Mock()
        state.begin_generation.side_effect = [True]
        state.finish_generation.return_value = None
        generator = mock.Mock()
        app = self.app_module.SlapPaperApp(
            generator=generator,
            state=state,
            listener=mock.Mock(),
            store=mock.Mock(),
            settings_store=mock.Mock(),
            thread_factory=InlineThread,
        )

        app.handle_manual_refresh()

        state.begin_generation.assert_called_once_with("manual")
        generator.generate.assert_called_once()

    def test_motto_change_handler_forces_resource_reload(self):
        generator = mock.Mock()
        app = self.app_module.SlapPaperApp(
            generator=generator,
            state=mock.Mock(),
            listener=mock.Mock(),
            store=mock.Mock(),
            settings_store=mock.Mock(),
        )

        app.handle_mottos_changed()

        generator.load_resources.assert_called_once_with(force=True)

    def test_popover_factory_receives_motto_change_handler(self):
        factory = mock.Mock(return_value=object())
        store = mock.Mock()
        settings_store = mock.Mock()
        app = self.app_module.SlapPaperApp(
            generator=mock.Mock(),
            state=mock.Mock(),
            listener=mock.Mock(),
            store=store,
            settings_store=settings_store,
            popover_controller_factory=factory,
        )

        controller = app._build_popover_controller()

        self.assertIsNotNone(controller)
        factory.assert_called_once_with(
            store,
            settings_store,
            app.handle_manual_refresh,
            app.stop,
            app.handle_mottos_changed,
        )

    def test_run_syncs_autostart_when_enabled(self):
        settings_store = mock.Mock()
        settings_store.get_setting.return_value = True
        app = self.app_module.SlapPaperApp(
            generator=mock.Mock(),
            state=mock.Mock(),
            listener=mock.Mock(),
            store=mock.Mock(),
            settings_store=settings_store,
        )

        with mock.patch.object(self.app_module, "set_autostart") as autostart_mock:
            with mock.patch.object(self.app_module, "AppKit"):
                with mock.patch.object(self.app_module, "AppHelper"):
                    with mock.patch.object(app, "_build_popover_controller"):
                        with mock.patch.object(app, "_tray_controller_factory"):
                            app.run()

        autostart_mock.assert_called_once_with(True)


if __name__ == "__main__":
    unittest.main()
