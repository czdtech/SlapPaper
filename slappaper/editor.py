from slappaper.store import MottoStore, SettingsStore
from slappaper.macos_utils import set_autostart, is_autostart_enabled

try:
    import objc
except Exception:
    objc = None

try:
    import AppKit
except Exception:
    AppKit = None


class MottoEditorModel:
    def __init__(self, store=None, settings_store=None, on_change=None):
        self.store = store or MottoStore()
        self.settings_store = settings_store or SettingsStore()
        self._on_change = on_change or (lambda: None)
        self.items = []
        self.editing_index = None
        self.status_message = ""
        self.status_is_error = False
        self.reload()

    def reload(self):
        try:
            self.items = self.store.load_mottos()
        except Exception as exc:
            self.items = []
            self.editing_index = None
            self.set_status(str(exc), is_error=True)

    def notify_change(self):
        self._on_change()

    def set_status(self, message, is_error=False):
        self.status_message = message
        self.status_is_error = is_error

    def add_motto(self, text):
        duplicate = text.strip() in self.items
        self.store.add_motto(text)
        self.reload()
        self.editing_index = None
        self.notify_change()
        if duplicate:
            self.set_status("已添加，但这条文案和现有内容重复。")
        else:
            self.set_status("文案已添加。")

    def start_edit(self, index):
        self.editing_index = index
        self.set_status("")

    def cancel_edit(self):
        self.editing_index = None
        self.set_status("")

    def save_edit(self, text):
        if self.editing_index is None:
            raise RuntimeError("No motto is being edited.")
        self.store.update_motto(self.editing_index, text)
        self.reload()
        self.editing_index = None
        self.notify_change()
        self.set_status("文案已保存。")

    def delete_motto(self, index):
        self.store.delete_motto(index)
        self.reload()
        self.editing_index = None
        self.notify_change()
        self.set_status("文案已删除。")

    @property
    def autostart_enabled(self):
        return self.settings_store.get_setting("autostart", False)

    def toggle_autostart(self, enabled):
        if set_autostart(enabled):
            self.settings_store.set_setting("autostart", enabled)
            state_str = "已开启" if enabled else "已关闭"
            self.set_status(f"开机自启{state_str}。")
        else:
            # If set_autostart fails, it might be because we're in dev mode
            self.settings_store.set_setting("autostart", enabled)
            self.set_status("自启设置已保存（仅在打包后的应用中生效）。")


if AppKit is not None and objc is not None:

    class MottoPopoverController(AppKit.NSViewController):
        WIDTH = 460
        HEIGHT = 460
        ROW_HEIGHT = 76
        EDIT_ROW_HEIGHT = 82

        def initWithStore_settingsStore_onRefresh_onQuit_onMottosChanged_(
            self,
            store,
            settings_store,
            on_refresh,
            on_quit,
            on_mottos_changed,
        ):
            self = objc.super(MottoPopoverController, self).init()
            if self is None:
                return None

            self._model = MottoEditorModel(
                store=store, settings_store=settings_store, on_change=on_mottos_changed
            )
            self._on_refresh = on_refresh
            self._on_quit = on_quit
            self._editor_fields = {}
            self._new_motto_field = None
            self._status_label = None
            self._scroll_view = None
            self._list_document_view = None
            self._autostart_checkbox = None
            self._pending_focus_field = None
            return self

        def loadView(self):
            # Use NSVisualEffectView for that modern macOS glass look
            vibrant_root = AppKit.NSVisualEffectView.alloc().initWithFrame_(
                AppKit.NSMakeRect(0, 0, self.WIDTH, self.HEIGHT)
            )
            vibrant_root.setMaterial_(AppKit.NSVisualEffectMaterialPopover)
            vibrant_root.setBlendingMode_(AppKit.NSVisualEffectBlendingModeBehindWindow)
            vibrant_root.setState_(AppKit.NSVisualEffectStateActive)
            self.setView_(vibrant_root)

            # Header Section
            title_label = self._make_label("文案库")
            title_label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(15))
            title_label.setFrame_(AppKit.NSMakeRect(20, self.HEIGHT - 38, 200, 22))
            vibrant_root.addSubview_(title_label)

            self._new_motto_field = AppKit.NSTextField.alloc().initWithFrame_(
                AppKit.NSMakeRect(20, self.HEIGHT - 76, 320, 28)
            )
            self._new_motto_field.setPlaceholderString_("新增一句文案...")
            self._new_motto_field.setBezelStyle_(AppKit.NSTextFieldRoundedBezel)
            vibrant_root.addSubview_(self._new_motto_field)

            add_button = self._make_symbol_button("plus.circle.fill", "添加", "addMotto:")
            add_button.setFrame_(AppKit.NSMakeRect(348, self.HEIGHT - 78, 92, 32))
            vibrant_root.addSubview_(add_button)

            self._status_label = self._make_label("")
            self._status_label.setFont_(AppKit.NSFont.systemFontOfSize_(11))
            self._status_label.setTextColor_(AppKit.NSColor.secondaryLabelColor())
            self._status_label.setFrame_(
                AppKit.NSMakeRect(22, self.HEIGHT - 104, 418, 16)
            )
            vibrant_root.addSubview_(self._status_label)

            # Main List Section
            self._scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(
                AppKit.NSMakeRect(16, 92, self.WIDTH - 32, self.HEIGHT - 204)
            )
            self._scroll_view.setHasVerticalScroller_(True)
            self._scroll_view.setBorderType_(AppKit.NSNoBorder)
            self._scroll_view.setDrawsBackground_(False)
            vibrant_root.addSubview_(self._scroll_view)

            self._list_document_view = AppKit.NSView.alloc().initWithFrame_(
                AppKit.NSMakeRect(0, 0, self.WIDTH - 48, 200)
            )
            self._scroll_view.setDocumentView_(self._list_document_view)

            # Footer Section
            # Auto-start checkbox with a more subtle look
            self._autostart_checkbox = AppKit.NSButton.checkboxWithTitle_target_action_(
                "登录时自动启动",
                self,
                "toggleAutostart:",
            )
            self._autostart_checkbox.setFont_(AppKit.NSFont.systemFontOfSize_(12))
            self._autostart_checkbox.setFrame_(AppKit.NSMakeRect(18, 54, 160, 24))
            self._autostart_checkbox.setState_(
                AppKit.NSOnState if self._model.autostart_enabled else AppKit.NSOffState
            )
            vibrant_root.addSubview_(self._autostart_checkbox)

            refresh_button = self._make_symbol_button("arrow.clockwise", "刷新壁纸", "refreshWallpaper:")
            refresh_button.setFrame_(AppKit.NSMakeRect(16, 16, 110, 32))
            vibrant_root.addSubview_(refresh_button)

            quit_button = self._make_button("退出", "quitApp:")
            quit_button.setFrame_(AppKit.NSMakeRect(self.WIDTH - 86, 16, 70, 32))
            vibrant_root.addSubview_(quit_button)

            self.reload()

        @objc.python_method
        def reload(self):
            self._model.reload()
            if self._scroll_view is None or self._list_document_view is None:
                return
            self._render_status()
            self._render_rows()
            if self._autostart_checkbox:
                self._autostart_checkbox.setState_(
                    AppKit.NSOnState
                    if self._model.autostart_enabled
                    else AppKit.NSOffState
                )

        @objc.python_method
        def _render_status(self):
            if self._status_label is None:
                return

            self._status_label.setStringValue_(self._model.status_message or "")
            color = (
                AppKit.NSColor.systemRedColor()
                if self._model.status_is_error
                else AppKit.NSColor.secondaryLabelColor()
            )
            self._status_label.setTextColor_(color)

        @objc.python_method
        def _render_rows(self):
            self._editor_fields = {}

            for subview in list(self._list_document_view.subviews()):
                subview.removeFromSuperview()

            rows = self._model.items
            total_height = 12
            for index in range(len(rows)):
                total_height += self._row_height(index) + 10
            total_height = max(total_height, self._scroll_view.contentSize().height)

            width = self._scroll_view.contentSize().width
            self._list_document_view.setFrame_(
                AppKit.NSMakeRect(0, 0, width, total_height)
            )

            current_y = total_height - 12
            for index, text in enumerate(rows):
                row_height = self._row_height(index)
                current_y -= row_height
                row_view = self._make_row_view(index, text, width, row_height)
                row_view.setFrame_(
                    AppKit.NSMakeRect(4, current_y, width - 8, row_height)
                )
                self._list_document_view.addSubview_(row_view)
                current_y -= 10

            if not rows:
                self._render_empty_state(width)

            if self._pending_focus_field is not None:
                field = self._pending_focus_field
                self._pending_focus_field = None
                window = self.view().window() if self.view() else None
                if window:
                    window.makeFirstResponder_(field)

        @objc.python_method
        def _render_empty_state(self, width):
            container = AppKit.NSView.alloc().initWithFrame_(
                AppKit.NSMakeRect(0, 0, width, 200)
            )
            
            # Big Icon
            if hasattr(AppKit.NSImage, "imageWithSystemSymbolName_accessibilityDescription_"):
                icon = AppKit.NSImage.imageWithSystemSymbolName_accessibilityDescription_(
                    "quote.bubble", None
                )
                if icon:
                    icon_view = AppKit.NSImageView.imageViewWithImage_(icon)
                    icon_view.setSymbolConfiguration_(
                        AppKit.NSImageSymbolConfiguration.configurationWithPointSize_weight_(48, AppKit.NSFontWeightLight)
                    )
                    icon_view.setContentTintColor_(AppKit.NSColor.tertiaryLabelColor())
                    icon_view.setFrame_(AppKit.NSMakeRect((width-60)/2, 80, 60, 60))
                    container.addSubview_(icon_view)

            empty_label = self._make_label("还没有文案，先在上方输入一句。")
            empty_label.setAlignment_(AppKit.NSCenterTextAlignment)
            empty_label.setTextColor_(AppKit.NSColor.tertiaryLabelColor())
            empty_label.setFrame_(AppKit.NSMakeRect(20, 50, width - 40, 20))
            container.addSubview_(empty_label)
            
            container.setFrameOrigin_(AppKit.NSMakePoint(0, (self._scroll_view.contentSize().height - 200) / 2))
            self._list_document_view.addSubview_(container)

        @objc.python_method
        def _row_height(self, index):
            return (
                self.EDIT_ROW_HEIGHT
                if self._model.editing_index == index
                else self.ROW_HEIGHT
            )

        @objc.python_method
        def _make_row_view(self, index, text, width, row_height):
            row = AppKit.NSView.alloc().initWithFrame_(
                AppKit.NSMakeRect(0, 0, width - 8, row_height)
            )

            # Use a slightly transparent background for rows
            background = AppKit.NSBox.alloc().initWithFrame_(row.bounds())
            background.setBoxType_(AppKit.NSBoxCustom)
            background.setBorderType_(AppKit.NSNoBorder)
            background.setCornerRadius_(12.0)
            background.setFillColor_(AppKit.NSColor.quaternaryLabelColor())
            background.setAutoresizingMask_(
                AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable
            )
            row.addSubview_(background)

            content_width = width - 24
            if self._model.editing_index == index:
                field = AppKit.NSTextField.alloc().initWithFrame_(
                    AppKit.NSMakeRect(12, row_height - 46, content_width - 130, 32)
                )
                field.setStringValue_(text)
                field.setBezelStyle_(AppKit.NSTextFieldRoundedBezel)
                row.addSubview_(field)
                self._editor_fields[index] = field

                save_button = self._make_button("保存", "saveEdit:")
                save_button.setTag_(index)
                save_button.setKeyEquivalent_("\r") # Enter to save
                save_button.setFrame_(
                    AppKit.NSMakeRect(content_width - 110, row_height - 46, 56, 32)
                )
                row.addSubview_(save_button)

                cancel_button = self._make_button("取消", "cancelEdit:")
                cancel_button.setTag_(index)
                cancel_button.setKeyEquivalent_("\x1b") # Esc to cancel
                cancel_button.setFrame_(
                    AppKit.NSMakeRect(content_width - 50, row_height - 46, 56, 32)
                )
                row.addSubview_(cancel_button)
                
                self._pending_focus_field = field

            else:
                label = self._make_multiline_label(text)
                label.setFrame_(
                    AppKit.NSMakeRect(14, 12, content_width - 90, row_height - 24)
                )
                row.addSubview_(label)

                # Use a more standard button style for visibility
                edit_btn = self._make_symbol_only_button("pencil", "编辑", "beginEdit:")
                edit_btn.setTag_(index)
                edit_btn.setFrame_(AppKit.NSMakeRect(content_width - 78, (row_height - 32) / 2, 36, 32))
                row.addSubview_(edit_btn)

                del_btn = self._make_symbol_only_button("trash", "删除", "deleteMotto:")
                del_btn.setTag_(index)
                del_btn.setFrame_(AppKit.NSMakeRect(content_width - 40, (row_height - 32) / 2, 36, 32))
                row.addSubview_(del_btn)

            return row

        @objc.python_method
        def _make_label(self, text):
            label = AppKit.NSTextField.labelWithString_(text)
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            label.setEditable_(False)
            label.setSelectable_(False)
            label.setTextColor_(AppKit.NSColor.labelColor())
            return label

        @objc.python_method
        def _make_multiline_label(self, text):
            label = self._make_label(text)
            label.setFont_(AppKit.NSFont.systemFontOfSize_(13))
            cell = label.cell()
            cell.setWraps_(True)
            cell.setScrollable_(False)
            cell.setLineBreakMode_(AppKit.NSLineBreakByWordWrapping)
            return label

        @objc.python_method
        def _make_button(self, title, action_name):
            button = (
                AppKit.NSButton.alloc().initWithFrame_(
                    AppKit.NSMakeRect(0, 0, 60, 32)
                )
            )
            button.setTitle_(title)
            button.setBezelStyle_(AppKit.NSRoundedBezelStyle)
            button.setTarget_(self)
            button.setAction_(action_name)
            return button

        @objc.python_method
        def _make_symbol_button(self, symbol_name, title, action_name):
            button = self._make_button(title, action_name)
            if hasattr(AppKit.NSImage, "imageWithSystemSymbolName_accessibilityDescription_"):
                img = AppKit.NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol_name, title)
                if img:
                    button.setImage_(img)
                    button.setImagePosition_(AppKit.NSImageLeft)
            return button

        @objc.python_method
        def _make_symbol_only_button(self, symbol_name, title, action_name):
            # Create a more visible button with symbol
            if hasattr(AppKit.NSButton, "buttonWithImage_target_action_") and hasattr(AppKit.NSImage, "imageWithSystemSymbolName_accessibilityDescription_"):
                img = AppKit.NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol_name, title)
                button = AppKit.NSButton.buttonWithImage_target_action_(img, self, action_name)
                button.setBezelStyle_(AppKit.NSRecessedBezelStyle)
                button.setToolTip_(title)
            else:
                button = self._make_button(title, action_name)
            
            button.setShowsBorderOnlyWhileMouseInside_(True)
            return button

        def addMotto_(self, sender):
            try:
                self._model.add_motto(self._new_motto_field.stringValue())
                self._new_motto_field.setStringValue_("")
            except Exception as exc:
                self._model.set_status(str(exc), is_error=True)
            self._render_status()
            self._render_rows()

        def beginEdit_(self, sender):
            self._model.start_edit(sender.tag())
            self._render_status()
            self._render_rows()

        def cancelEdit_(self, sender):
            self._model.cancel_edit()
            self._render_status()
            self._render_rows()

        def saveEdit_(self, sender):
            try:
                field = self._editor_fields[sender.tag()]
                self._model.save_edit(field.stringValue())
            except Exception as exc:
                self._model.set_status(str(exc), is_error=True)
            self._render_status()
            self._render_rows()

        def deleteMotto_(self, sender):
            alert = AppKit.NSAlert.alloc().init()
            alert.setMessageText_("删除这条文案？")
            alert.setInformativeText_("删除后会立即从文案库中移除。")
            alert.addButtonWithTitle_("删除")
            alert.addButtonWithTitle_("取消")
            alert.setAlertStyle_(AppKit.NSAlertStyleCritical)
            if alert.runModal() == AppKit.NSAlertFirstButtonReturn:
                try:
                    self._model.delete_motto(sender.tag())
                except Exception as exc:
                    self._model.set_status(str(exc), is_error=True)
                self._render_status()
                self._render_rows()

        def toggleAutostart_(self, sender):
            enabled = sender.state() == AppKit.NSOnState
            self._model.toggle_autostart(enabled)
            self._render_status()

        def refreshWallpaper_(self, sender):
            self._on_refresh()

        def quitApp_(self, sender):
            self._on_quit()

    def create_motto_popover_controller(
        store, settings_store, on_refresh, on_quit, on_mottos_changed
    ):
        return MottoPopoverController.alloc().initWithStore_settingsStore_onRefresh_onQuit_onMottosChanged_(
            store,
            settings_store,
            on_refresh,
            on_quit,
            on_mottos_changed,
        )
else:

    class MottoPopoverController:  # pragma: no cover - non-mac fallback
        pass

    def create_motto_popover_controller(  # pragma: no cover
        store,
        settings_store,
        on_refresh,
        on_quit,
        on_mottos_changed,
    ):
        raise RuntimeError("AppKit is unavailable on this platform.")
