import pathlib
import subprocess
import sys
import textwrap
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def run_import_without_pyobjc(module_name):
    script = textwrap.dedent(
        f"""
        import builtins
        import sys

        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in {{"objc", "AppKit"}}:
                raise ModuleNotFoundError(name)
            return original_import(name, globals, locals, fromlist, level)

        builtins.__import__ = fake_import
        sys.path.insert(0, {str(PROJECT_ROOT)!r})
        sys.modules.pop({module_name!r}, None)
        module = __import__({module_name!r}, fromlist=["*"])
        assert getattr(module, "AppKit", None) is None
        print("ok")
        """
    )
    return subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )


class ImportFallbackTests(unittest.TestCase):
    def test_editor_import_succeeds_without_pyobjc(self):
        result = run_import_without_pyobjc("slappaper.editor")

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_app_import_succeeds_without_pyobjc(self):
        result = run_import_without_pyobjc("slappaper.app")

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
