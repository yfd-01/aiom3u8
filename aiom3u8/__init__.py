from .api import download, download_coro
from .core import Core


__title__ = "aiom3u8"
__version__ = "1.0.0"
__description__ = "Using async way to download a video file by parsing m3u8 file"
__url__ = "https://github.com/yfd-01/aiom3u8"
__author__ = "yfd"
__author_email__ = "yunxiaofeng2019@gmail.com"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2022 yfd"

__all__ = (
    "download",
    "download_coro",
    "Core"
)
