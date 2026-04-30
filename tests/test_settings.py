import json
import unittest
import tempfile
from pathlib import Path
from slappaper.store import SettingsStore


class SettingsStoreTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.test_dir.name) / "settings.json"
        self.store = SettingsStore(path=self.path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_load_returns_empty_dict_when_missing(self):
        self.assertEqual(self.store.load_settings(), {})

    def test_set_and_get_setting(self):
        self.store.set_setting("test_key", "test_value")
        self.assertEqual(self.store.get_setting("test_key"), "test_value")

    def test_get_default_value(self):
        self.assertEqual(self.store.get_setting("non_existent", "default"), "default")

    def test_persistence(self):
        self.store.set_setting("active", True)
        
        # New store instance with same path
        new_store = SettingsStore(path=self.path)
        self.assertTrue(new_store.get_setting("active"))


if __name__ == "__main__":
    unittest.main()
