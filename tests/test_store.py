import importlib
import json
import pathlib
import tempfile
import unittest
from unittest import mock


def load_store_module():
    return importlib.import_module("slappaper.store")


class MottoStoreTests(unittest.TestCase):
    def setUp(self):
        self.store_module = load_store_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.motto_path = pathlib.Path(self.temp_dir.name) / "motto.json"
        self.motto_path.write_text(
            json.dumps(
                [
                    "收藏了不代表学会了，那只是你逃避思考的避难所。",
                    "你的收藏夹是知识的坟场，不是进化的阶梯。",
                ],
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.store = self.store_module.MottoStore(path=self.motto_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_motto_appends_trimmed_text(self):
        self.store.add_motto("  工具无法拯救你的平庸，只有产出可以。  ")

        mottos = json.loads(self.motto_path.read_text(encoding="utf-8"))
        self.assertEqual(mottos[-1], "工具无法拯救你的平庸，只有产出可以。")

    def test_update_motto_rewrites_existing_entry(self):
        self.store.update_motto(0, "买课带来的成长感是廉价的幻觉，只有敲代码才是痛苦的真实。")

        mottos = json.loads(self.motto_path.read_text(encoding="utf-8"))
        self.assertEqual(mottos[0], "买课带来的成长感是廉价的幻觉，只有敲代码才是痛苦的真实。")

    def test_delete_motto_removes_entry(self):
        self.store.delete_motto(1)

        mottos = json.loads(self.motto_path.read_text(encoding="utf-8"))
        self.assertEqual(
            mottos,
            ["收藏了不代表学会了，那只是你逃避思考的避难所。"],
        )

    def test_empty_text_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add_motto("   ")

    def test_default_store_path_uses_application_support_on_macos(self):
        fake_home = pathlib.Path("/tmp/slappaper-home")

        path = self.store_module.get_store_path(system_name="Darwin", home=fake_home)

        self.assertEqual(
            path,
            fake_home / "Library" / "Application Support" / "SlapPaper" / "motto.json",
        )

    def test_missing_user_file_reads_bundled_defaults_without_creating_user_file(self):
        user_path = pathlib.Path(self.temp_dir.name) / "user" / "motto.json"
        bundled_path = pathlib.Path(self.temp_dir.name) / "bundled.json"
        bundled_path.write_text(
            json.dumps(["  先做出来再说。  ", ""], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        store = self.store_module.MottoStore(path=user_path, bundled_path=bundled_path)

        mottos = store.load_mottos()

        self.assertEqual(mottos, ["先做出来再说。"])
        self.assertFalse(user_path.exists())

    def test_invalid_user_file_raises_and_is_not_overwritten(self):
        bad_path = pathlib.Path(self.temp_dir.name) / "broken.json"
        bad_path.write_text("{ not json", encoding="utf-8")
        store = self.store_module.MottoStore(path=bad_path, bundled_path=self.motto_path)

        with self.assertRaises(self.store_module.MottoStoreError):
            store.load_mottos()

        with self.assertRaises(self.store_module.MottoStoreError):
            store.add_motto("新文案")

        self.assertEqual(bad_path.read_text(encoding="utf-8"), "{ not json")


if __name__ == "__main__":
    unittest.main()
