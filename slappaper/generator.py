import os
import platform
import random
import sys
import time
from functools import lru_cache

from slappaper.config import (
    DEFAULT_HEIGHT,
    DEFAULT_MOTTOS,
    DEFAULT_WIDTH,
    LEADING_PUNCTUATION,
    LINE_SPACING,
    LOG_MAX_BYTES,
    LOG_PATH,
    MACOS_FONT_NAMES,
    MAX_LINE_COUNT,
    MAX_TEXT_WIDTH_RATIO,
    STORAGE_DIR,
    SUPPORTED_PLATFORM,
    WORD_JOINERS,
)
from slappaper.store import MottoStore

try:
    import AppKit
except Exception:
    AppKit = None


def log(message):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    try:
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > LOG_MAX_BYTES:
            with open(LOG_PATH, "rb") as f:
                f.seek(-LOG_MAX_BYTES // 2, 2)
                tail = f.read()
            with open(LOG_PATH, "wb") as f:
                f.write(tail[tail.find(b"\n") + 1:])
    except OSError:
        pass
    with open(LOG_PATH, "a", encoding="utf-8") as file_obj:
        file_obj.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")


def ensure_storage_dir(storage_dir=STORAGE_DIR):
    os.makedirs(storage_dir, exist_ok=True)


def get_base_path():
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ensure_supported_platform(system_name=None):
    system_name = system_name or platform.system()
    if system_name != SUPPORTED_PLATFORM:
        raise RuntimeError("SlapPaper currently supports macOS only.")


def get_main_screen():
    if AppKit is None or platform.system() != SUPPORTED_PLATFORM:
        return None

    try:
        return AppKit.NSScreen.mainScreen() or (
            AppKit.NSScreen.screens()[0] if AppKit.NSScreen.screens() else None
        )
    except Exception as exc:
        log(f"Screen detection failed: {exc}")
        return None


def get_target_dimensions(screen=None):
    if platform.system() != SUPPORTED_PLATFORM:
        return DEFAULT_WIDTH, DEFAULT_HEIGHT

    screen = screen or get_main_screen()
    if screen is None:
        return DEFAULT_WIDTH, DEFAULT_HEIGHT

    frame = screen.frame()
    scale = screen.backingScaleFactor() if hasattr(screen, "backingScaleFactor") else 1.0
    width = max(1, int(frame.size.width * scale))
    height = max(1, int(frame.size.height * scale))
    return width, height


def get_font_size(target_height):
    return max(96, int(target_height * 0.074))


def measure_text(font, text):
    if hasattr(font, "getlength"):
        return float(font.getlength(text))
    if not text:
        return 0.0
    if AppKit is None:
        return float(len(text))
    ns_string = AppKit.NSString.stringWithString_(text)
    attrs = {AppKit.NSFontAttributeName: font}
    return float(ns_string.sizeWithAttributes_(attrs).width)


def can_break_between(text, index):
    if index <= 0 or index >= len(text):
        return True

    previous_char = text[index - 1]
    current_char = text[index]

    if current_char in LEADING_PUNCTUATION:
        return False

    if previous_char.isspace() or current_char.isspace():
        return True

    previous_is_word = previous_char.isascii() and (
        previous_char.isalnum() or previous_char in WORD_JOINERS
    )
    current_is_word = current_char.isascii() and (
        current_char.isalnum() or current_char in WORD_JOINERS
    )
    return not (previous_is_word and current_is_word)


def line_penalty(segment, width, max_width, is_last_line):
    visible_length = len(segment.replace(" ", ""))
    slack = max_width - width
    penalty = slack * slack

    if is_last_line:
        penalty *= 0.35
        if visible_length <= 2:
            penalty += max_width * max_width
    elif visible_length <= 1:
        penalty += max_width * max_width

    return penalty


def wrap_text_lines(text, font, max_width, max_lines=MAX_LINE_COUNT):
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    break_points = [0]
    break_points.extend(index for index in range(1, len(cleaned)) if can_break_between(cleaned, index))
    break_points.append(len(cleaned))

    @lru_cache(maxsize=None)
    def solve(start_index, lines_left):
        best = None

        for end_index in break_points:
            if end_index <= start_index:
                continue

            segment = cleaned[start_index:end_index].strip()
            if not segment:
                continue

            width = measure_text(font, segment)
            if width > max_width:
                continue

            is_last_line = end_index == len(cleaned)
            if not is_last_line and lines_left == 1:
                continue

            candidate_penalty = line_penalty(segment, width, max_width, is_last_line)
            if is_last_line:
                candidate = (candidate_penalty, [segment])
            else:
                rest = solve(end_index, lines_left - 1)
                if rest is None:
                    continue
                candidate = (candidate_penalty + rest[0], [segment] + rest[1])

            if best is None or candidate[0] < best[0]:
                best = candidate

        return best

    best_solution = None
    for line_count in range(1, max_lines + 1):
        candidate = solve(0, line_count)
        if candidate is None:
            continue
        if best_solution is None or candidate[0] < best_solution[0]:
            best_solution = candidate

    if best_solution is None:
        return [cleaned]
    return best_solution[1]


class WallpaperGenerator:
    def __init__(self, storage_dir=STORAGE_DIR, motto_store=None):
        self.storage_dir = storage_dir
        self.motto_store = motto_store or MottoStore()
        self._font = None
        self._font_size = None
        self._mottos = []

    def ensure_supported_platform(self):
        ensure_supported_platform()

    def get_target_dimensions(self):
        return get_target_dimensions()

    def load_mottos(self):
        mottos = self.motto_store.load_runtime_mottos()
        if not mottos:
            log("Motto store returned no usable phrases; using built-in fallback.")
            return DEFAULT_MOTTOS.copy()
        return mottos

    def load_font(self, font_size):
        if AppKit is None:
            raise RuntimeError("AppKit is unavailable; cannot load font.")
        for name in MACOS_FONT_NAMES:
            font = AppKit.NSFont.fontWithName_size_(name, font_size)
            if font is not None:
                return font
        log("Falling back to NSFont.systemFontOfSize.")
        return AppKit.NSFont.systemFontOfSize_(font_size)

    def load_resources(self, force=False):
        _, target_height = self.get_target_dimensions()
        target_font_size = get_font_size(target_height)

        if (
            not force
            and self._font is not None
            and self._mottos
            and self._font_size == target_font_size
        ):
            return

        log("Loading resources...")
        self._mottos = self.load_mottos()
        self._font = self.load_font(target_font_size)
        self._font_size = target_font_size

    def cleanup_previous_wallpapers(self):
        ensure_storage_dir(self.storage_dir)
        for filename in os.listdir(self.storage_dir):
            if not filename.startswith("slappaper_"):
                continue
            try:
                os.remove(os.path.join(self.storage_dir, filename))
            except OSError:
                continue

    def render_wallpaper(self, wrapped_text, width, height, output_path):
        if AppKit is None:
            raise RuntimeError("AppKit is unavailable; cannot render wallpaper.")

        bitmap = AppKit.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None, width, height, 8, 4, True, False,
            AppKit.NSDeviceRGBColorSpace, 0, 0,
        )
        if bitmap is None:
            raise RuntimeError("Failed to allocate NSBitmapImageRep.")

        context = AppKit.NSGraphicsContext.graphicsContextWithBitmapImageRep_(bitmap)
        AppKit.NSGraphicsContext.saveGraphicsState()
        AppKit.NSGraphicsContext.setCurrentContext_(context)
        try:
            AppKit.NSColor.blackColor().set()
            AppKit.NSBezierPath.fillRect_(AppKit.NSMakeRect(0, 0, width, height))

            paragraph = AppKit.NSMutableParagraphStyle.alloc().init()
            paragraph.setAlignment_(AppKit.NSTextAlignmentCenter)
            paragraph.setLineSpacing_(LINE_SPACING)

            attrs = {
                AppKit.NSFontAttributeName: self._font,
                AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor(),
                AppKit.NSParagraphStyleAttributeName: paragraph,
            }

            ns_text = AppKit.NSString.stringWithString_(wrapped_text)
            bounding = ns_text.boundingRectWithSize_options_attributes_(
                AppKit.NSMakeSize(width, height),
                AppKit.NSStringDrawingUsesLineFragmentOrigin,
                attrs,
            )
            text_height = bounding.size.height
            rect = AppKit.NSMakeRect(0, (height - text_height) / 2, width, text_height)
            ns_text.drawInRect_withAttributes_(rect, attrs)
        finally:
            AppKit.NSGraphicsContext.restoreGraphicsState()

        png_data = bitmap.representationUsingType_properties_(
            AppKit.NSBitmapImageFileTypePNG, {}
        )
        if png_data is None:
            raise RuntimeError("Failed to encode PNG data.")
        if not png_data.writeToFile_atomically_(output_path, True):
            raise RuntimeError(f"Failed to write PNG to {output_path}.")

    def set_wallpaper(self, path):
        if AppKit is None:
            raise RuntimeError("AppKit is unavailable; cannot set wallpaper.")

        from Foundation import NSURL

        url = NSURL.fileURLWithPath_(path)
        workspace = AppKit.NSWorkspace.sharedWorkspace()
        screens = list(AppKit.NSScreen.screens() or [])
        if not screens:
            raise RuntimeError("No screens detected; cannot set wallpaper.")

        failures = 0
        for screen in screens:
            success, error = workspace.setDesktopImageURL_forScreen_options_error_(
                url, screen, {}, None
            )
            if not success:
                failures += 1
                log(f"setDesktopImageURL failed on one screen: {error}")

        if failures == len(screens):
            raise RuntimeError(
                f"Failed to set wallpaper on all {len(screens)} screens."
            )

    def generate(self):
        self.ensure_supported_platform()
        ensure_storage_dir(self.storage_dir)
        self.load_resources()
        if not self._mottos:
            raise RuntimeError("No mottos available for rendering.")

        width, height = self.get_target_dimensions()
        text = random.choice(self._mottos)
        self.cleanup_previous_wallpapers()

        output_path = os.path.join(self.storage_dir, f"slappaper_{int(time.time())}.png")
        max_text_width = width * MAX_TEXT_WIDTH_RATIO
        lines = wrap_text_lines(text, self._font, max_text_width)
        wrapped_text = "\n".join(lines)

        self.render_wallpaper(wrapped_text, width, height, output_path)
        self.set_wallpaper(output_path)
        log(f"Wallpaper ready: {text[:24]}...")
        return output_path
