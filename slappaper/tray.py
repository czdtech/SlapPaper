try:
    import objc
except Exception:
    objc = None

try:
    import AppKit
except Exception:
    AppKit = None


if AppKit is not None and objc is not None:
    class StatusBarController(AppKit.NSObject):
        def initWithPopoverController_(self, popover_controller):
            self = objc.super(StatusBarController, self).init()
            if self is None:
                return None

            self._popover_controller = popover_controller
            self._popover = AppKit.NSPopover.alloc().init()
            self._popover.setBehavior_(AppKit.NSPopoverBehaviorTransient)
            self._popover.setContentViewController_(popover_controller)

            self._status_bar = AppKit.NSStatusBar.systemStatusBar()
            self._status_item = self._status_bar.statusItemWithLength_(AppKit.NSVariableStatusItemLength)
            button = self._status_item.button()
            button.setTarget_(self)
            button.setAction_("togglePopover:")
            
            # Use our custom "SP" branding icon
            icon_name = "tray_icon.png"
            from slappaper.store import get_bundle_base_path
            icon_path = get_bundle_base_path() / icon_name
            
            image = AppKit.NSImage.alloc().initWithContentsOfFile_(str(icon_path))
            if image:
                image.setTemplate_(True)
                button.setImage_(image)
            else:
                button.setTitle_("SP")
            
            return self

        def togglePopover_(self, sender):
            if self._popover.isShown():
                self._popover.performClose_(sender)
                return

            self._popover_controller.reload()
            self._popover.showRelativeToRect_ofView_preferredEdge_(
                sender.bounds(),
                sender,
                AppKit.NSMinYEdge,
            )

        @objc.python_method
        def stop(self):
            if self._popover.isShown():
                self._popover.performClose_(None)
            self._status_bar.removeStatusItem_(self._status_item)


    def create_status_bar_controller(popover_controller):
        return StatusBarController.alloc().initWithPopoverController_(popover_controller)
else:
    class StatusBarController:  # pragma: no cover - non-mac fallback
        pass

    def create_status_bar_controller(popover_controller):  # pragma: no cover
        raise RuntimeError("AppKit is unavailable on this platform.")
