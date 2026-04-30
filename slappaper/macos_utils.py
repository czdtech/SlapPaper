import subprocess
import sys
from pathlib import Path


def get_app_bundle_path():
    """
    Returns the path to the .app bundle if running as a frozen application.
    Otherwise returns None.
    """
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable)
        # Typical macOS bundle structure: SlapPaper.app/Contents/MacOS/SlapPaper
        if len(exe_path.parts) >= 3 and exe_path.parts[-3] == "Contents":
            return exe_path.parent.parent.parent
        return exe_path
    return None


def set_autostart(enabled, app_name="SlapPaper"):
    """
    Enables or disables auto-start by adding/removing the app from Login Items.
    Returns True if successful.
    """
    app_path = get_app_bundle_path()
    if not app_path:
        # Development mode: we don't want to register the python interpreter as a login item.
        return False

    app_path_str = str(app_path.absolute())

    if enabled:
        # First try to remove any existing item with the same name to avoid duplicates
        set_autostart(False, app_name)
        script = f'tell application "System Events" to make login item at end with properties {{path:"{app_path_str}", hidden:false, name:"{app_name}"}}'
    else:
        script = f'tell application "System Events" to delete every login item whose name is "{app_name}"'

    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def is_autostart_enabled(app_name="SlapPaper"):
    """
    Checks if the app is currently in the Login Items list.
    """
    script = f'tell application "System Events" to get name of every login item'
    try:
        result = subprocess.run(
            ["osascript", "-e", script], check=True, capture_output=True, text=True
        )
        items = [item.strip() for item in result.stdout.split(",")]
        return app_name in items
    except subprocess.CalledProcessError:
        return False
