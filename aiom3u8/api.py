import asyncio

from typing import Coroutine
from .core import Core


def download(m3u8, video_path, video_name, **kwargs) -> None:
    """
    start to download a video resource which pointed by a m3u8 url in a async way
    """

    with Core(m3u8, video_path, video_name, **kwargs) as core:
        asyncio.run(core.download())


def download_coro(m3u8, video_path, video_name, **kwargs) -> Coroutine:
    """ get a download coroutine """

    return Core(m3u8, video_path, video_name, **kwargs).download()
