import os


APP_NAME = "SlapPaper"
SUPPORTED_PLATFORM = "Darwin"
FINDER_BUNDLE_ID = "com.apple.finder"
LOG_PATH = os.path.join(
    os.path.expanduser("~/Library/Application Support"), APP_NAME, "debug.log"
)
LOG_MAX_BYTES = 512 * 1024  # 512 KB

DEFAULT_WIDTH = 3840
DEFAULT_HEIGHT = 2160
DEFAULT_MOTTOS = [
    "收藏了不代表学会了，那只是你逃避思考的避难所。",
    "你的收藏夹是知识的坟场，不是进化的阶梯。",
    "GitHub 上的 Star 越多，你离真正的代码就越远。",
    "买课带来的成长感是廉价的幻觉，只有敲代码才是痛苦的真实。",
    "工具无法拯救你的平庸，只有产出可以。",
]
MACOS_FONT_NAMES = [
    "PingFangSC-Regular",
    "STHeitiSC-Medium",
]

MAX_TEXT_WIDTH_RATIO = 0.8
MAX_LINE_COUNT = 3
LINE_SPACING = 40
AUTO_DEBOUNCE_SECONDS = 1.0
LEADING_PUNCTUATION = set("，。！？；：、”’）》】,.!?;:)]}")
WORD_JOINERS = set("-_./+#")
STORAGE_DIR = os.path.join(
    os.path.expanduser("~/Library/Application Support"), APP_NAME
)
