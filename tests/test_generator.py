import importlib
import types
import unittest
from unittest import mock


def load_generator_module():
    return importlib.import_module("slappaper.generator")


class FakeFont:
    def getlength(self, text):
        return float(len(text))


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.generator = load_generator_module()

    def test_wrap_text_balances_lines_without_orphaned_punctuation(self):
        text = "GitHub 上的 Star 越多，你离真正的代码就越远。"

        lines = self.generator.wrap_text_lines(text, FakeFont(), max_width=20)

        self.assertGreater(len(lines), 1)
        self.assertTrue(all(len(line.strip()) > 1 for line in lines))
        self.assertTrue(all(not line.startswith(("，", "。", "！", "？")) for line in lines[1:]))
        self.assertTrue(all(FakeFont().getlength(line) <= 20 for line in lines))

    def test_load_resources_uses_builtin_fallback_when_json_missing(self):
        generator = self.generator.WallpaperGenerator()
        fake_font = FakeFont()

        with mock.patch.object(self.generator, "get_base_path", return_value="/tmp/slappaper-missing"):
            with mock.patch.object(self.generator.platform, "system", return_value="Darwin"):
                with mock.patch.object(generator, "load_font", return_value=fake_font):
                    generator.load_resources(force=True)

        self.assertGreater(len(generator._mottos), 0)
        self.assertIs(generator._font, fake_font)

    def test_get_target_dimensions_uses_main_screen_scale(self):
        screen = types.SimpleNamespace(
            frame=lambda: types.SimpleNamespace(size=types.SimpleNamespace(width=1512, height=982)),
            backingScaleFactor=lambda: 2.0,
        )

        with mock.patch.object(self.generator.platform, "system", return_value="Darwin"):
            with mock.patch.object(self.generator, "get_main_screen", return_value=screen):
                size = self.generator.get_target_dimensions()

        self.assertEqual(size, (3024, 1964))

    def test_generate_invokes_render_and_set_wallpaper(self):
        generator = self.generator.WallpaperGenerator()
        generator._font = FakeFont()
        generator._mottos = ["工具无法拯救你的平庸，只有产出可以。"]
        generator._font_size = 128

        with mock.patch.object(generator, "ensure_supported_platform"):
            with mock.patch.object(generator, "load_resources"):
                with mock.patch.object(generator, "get_target_dimensions", return_value=(1440, 900)):
                    with mock.patch.object(generator, "cleanup_previous_wallpapers"):
                        with mock.patch.object(generator, "render_wallpaper") as render_mock:
                            with mock.patch.object(generator, "set_wallpaper") as set_mock:
                                output = generator.generate()

        self.assertTrue(output.endswith(".png"))
        render_mock.assert_called_once()
        args, _ = render_mock.call_args
        wrapped_text, width, height, path_arg = args
        self.assertEqual((width, height), (1440, 900))
        self.assertEqual(path_arg, output)
        self.assertIn("工具", wrapped_text)
        set_mock.assert_called_once_with(output)


if __name__ == "__main__":
    unittest.main()
