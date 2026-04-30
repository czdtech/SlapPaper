import importlib
import unittest
from unittest import mock


def load_editor_module():
    return importlib.import_module("slappaper.editor")


class FakeStore:
    def __init__(self, fail_on_load=False):
        self.mottos = [
            "收藏了不代表学会了，那只是你逃避思考的避难所。",
            "你的收藏夹是知识的坟场，不是进化的阶梯。",
        ]
        self.fail_on_load = fail_on_load

    def load_mottos(self):
        if self.fail_on_load:
            raise RuntimeError("broken motto file")
        return list(self.mottos)

    def add_motto(self, text):
        self.mottos.append(text)

    def update_motto(self, index, text):
        self.mottos[index] = text

    def delete_motto(self, index):
        self.mottos.pop(index)


class FakeSettingsStore:
    def __init__(self):
        self.settings = {}

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value


class MottoEditorModelTests(unittest.TestCase):
    def setUp(self):
        self.editor_module = load_editor_module()
        self.store = FakeStore()
        self.settings_store = FakeSettingsStore()
        self.model = self.editor_module.MottoEditorModel(
            store=self.store, settings_store=self.settings_store
        )

    def test_add_motto_refreshes_items(self):
        self.model.add_motto("工具无法拯救你的平庸，只有产出可以。")

        self.assertEqual(self.model.items[-1], "工具无法拯救你的平庸，只有产出可以。")
        self.assertIsNone(self.model.editing_index)

    def test_start_and_cancel_edit_track_single_row(self):
        self.model.start_edit(1)
        self.assertEqual(self.model.editing_index, 1)

        self.model.cancel_edit()
        self.assertIsNone(self.model.editing_index)

    def test_save_edit_updates_selected_row(self):
        self.model.start_edit(0)
        self.model.save_edit("买课带来的成长感是廉价的幻觉，只有敲代码才是痛苦的真实。")

        self.assertEqual(
            self.model.items[0],
            "买课带来的成长感是廉价的幻觉，只有敲代码才是痛苦的真实。",
        )
        self.assertIsNone(self.model.editing_index)

    def test_delete_motto_resets_editing_state(self):
        self.model.start_edit(1)
        self.model.delete_motto(1)

        self.assertEqual(
            self.model.items,
            ["收藏了不代表学会了，那只是你逃避思考的避难所。"],
        )
        self.assertIsNone(self.model.editing_index)

    def test_add_edit_delete_trigger_change_callback(self):
        on_change = mock.Mock()
        model = self.editor_module.MottoEditorModel(
            store=self.store, settings_store=self.settings_store, on_change=on_change
        )

        model.add_motto("工具无法拯救你的平庸，只有产出可以。")
        model.start_edit(0)
        model.save_edit("新的文案")
        model.delete_motto(1)

        self.assertEqual(on_change.call_count, 3)

    def test_reload_keeps_app_alive_when_store_is_invalid(self):
        broken_store = FakeStore(fail_on_load=True)

        model = self.editor_module.MottoEditorModel(
            store=broken_store, settings_store=self.settings_store
        )

        self.assertEqual(model.items, [])
        self.assertTrue(model.status_is_error)
        self.assertIn("broken motto file", model.status_message)

    def test_toggle_autostart_updates_store_and_status(self):
        with mock.patch.object(self.editor_module, "set_autostart", return_value=True):
            self.model.toggle_autostart(True)

        self.assertTrue(self.settings_store.get_setting("autostart"))
        self.assertIn("已开启", self.model.status_message)

    @unittest.skipIf(load_editor_module().AppKit is None, "AppKit runtime unavailable")
    def test_popover_reload_before_load_view_does_not_crash(self):
        self.editor_module.AppKit.NSApplication.sharedApplication()
        controller = self.editor_module.create_motto_popover_controller(
            self.store,
            self.settings_store,
            lambda sender=None: None,
            lambda sender=None: None,
            lambda: None,
        )

        controller.reload()

        self.assertEqual(
            controller._model.items,
            [
                "收藏了不代表学会了，那只是你逃避思考的避难所。",
                "你的收藏夹是知识的坟场，不是进化的阶梯。",
            ],
        )


if __name__ == "__main__":
    unittest.main()
