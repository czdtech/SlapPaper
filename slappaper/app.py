import threading

from slappaper.generator import WallpaperGenerator, ensure_supported_platform, log
from slappaper.listener import FinderActivationListener
from slappaper.state import ExecutionState
from slappaper.store import MottoStore, SettingsStore
from slappaper.editor import create_motto_popover_controller
from slappaper.tray import create_status_bar_controller
from slappaper.macos_utils import set_autostart

try:
    import AppKit
    from PyObjCTools import AppHelper
except Exception:
    AppKit = None
    AppHelper = None


class SlapPaperApp:
    def __init__(
        self,
        generator=None,
        state=None,
        listener=None,
        store=None,
        settings_store=None,
        thread_factory=threading.Thread,
        popover_controller_factory=create_motto_popover_controller,
        tray_controller_factory=create_status_bar_controller,
    ):
        self.store = store or MottoStore()
        self.settings_store = settings_store or SettingsStore()
        self.generator = generator or WallpaperGenerator(motto_store=self.store)
        self.state = state or ExecutionState()
        self.thread_factory = thread_factory
        self._popover_controller_factory = popover_controller_factory
        self._tray_controller_factory = tray_controller_factory
        self.listener = listener or FinderActivationListener(
            on_finder_activated=self.handle_finder_activated,
            logger=log,
        )
        self._tray_controller = None

    def handle_finder_activated(self):
        self._request_generation("auto")

    def handle_manual_refresh(self, sender=None):
        self._request_generation("manual")

    def handle_mottos_changed(self):
        try:
            self.generator.load_resources(force=True)
        except Exception as exc:
            log(f"Resource reload after motto edit failed: {exc}")

    def _request_generation(self, source):
        if not self.state.begin_generation(source):
            return False

        thread = self.thread_factory(target=lambda: self._run_generation(source), daemon=True)
        thread.start()
        return True

    def _run_generation(self, source):
        try:
            self.generator.generate()
        except Exception as exc:
            log(f"{source} generation failed: {exc}")
        finally:
            self.state.finish_generation()

    def stop(self, sender=None):
        self.listener.stop()
        if self._tray_controller is not None:
            self._tray_controller.stop()
            self._tray_controller = None
        if AppKit is not None:
            AppKit.NSApp().terminate_(None)

    def _build_popover_controller(self):
        return self._popover_controller_factory(
            self.store,
            self.settings_store,
            self.handle_manual_refresh,
            self.stop,
            self.handle_mottos_changed,
        )

    def run(self):
        ensure_supported_platform()
        if AppKit is None or AppHelper is None:
            raise RuntimeError("AppKit runtime is unavailable.")

        application = AppKit.NSApplication.sharedApplication()
        application.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

        try:
            self.listener.start()
        except Exception as exc:
            log(f"Listener start failed; falling back to manual-only mode: {exc}")

        # Sync autostart if enabled in settings (best effort)
        if self.settings_store.get_setting("autostart", False):
            set_autostart(True)

        self.generator.load_resources()
        popover_controller = self._build_popover_controller()
        self._tray_controller = self._tray_controller_factory(popover_controller)
        AppHelper.runEventLoop()


def main():
    app = SlapPaperApp()
    app.run()
