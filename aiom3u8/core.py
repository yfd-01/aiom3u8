# -*- coding: utf-8 -*-
import sys
import os
import functools

import aiohttp
import asyncio

from asyncio.tasks import Task
from asyncio.exceptions import TimeoutError
from aiohttp.client import ClientError
from tqdm import tqdm
from queue import SimpleQueue
from Crypto.Cipher import AES
from typing import (
    Optional,
    Mapping,
    Union
)

from .session import _get
from .parse import Parse
from .merge import Merge
from .params_def import (
    EXIT_MIDWAY,
    MAIN_ASYNC_TASK_SYMBOL,
    ASYNC_TASKS_MAINTAIN,
    INSPECT_INTERVAL,
    FETCH_FAILURE_TRIES,
    FILE_SC
)

if sys.platform.startswith('win'):
    if sys.version_info >= (3, 8):
        # window policy
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# else:
#     import uvloop
#     # others os policy
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class Core:
    __slots__ = (
        "_m3u8_url",
        "_host_url",
        "_prefix_url",
        "_video_path",
        "_video_name",
        "_params",
        "_cookies",
        "_headers",
        "_proxy",
        "_AUTO_HIGHEST_BANDWIDTH",
        "_async_tasks_maintain",
        "_inspect_interval",
        "_slices_urls",
        "_slices_urls_failure",
        "_slices_index_urls_ref",
        "_slices_total_num",
        "_slices_done_count",
        "_failure_retries",
        "_failure_tries_count",
        "_merge",
        "_progress_bar",
        "_progress_bar_display",
        "_decrypt_key"
    )

    def __init__(
        self,
        m3u8_url: str,
        video_path: str,
        video_name: str,
        *,
        video_name_extension: Optional[str] = ".mp4",
        params: Optional[Mapping[str, str]] = None,
        cookies: Optional[Mapping[str, str]] = None,
        headers: Optional[Mapping[str, str]] = None,
        proxy: Optional[str] = None,
        auto_highest_bandwidth: Optional[bool] = False,
        progress_bar_display: Optional[bool] = True,
        async_tasks_maintain: Optional[int] = ASYNC_TASKS_MAINTAIN,
        inspect_interval: Optional[float] = INSPECT_INTERVAL,
        failure_retries: Optional[int] = FETCH_FAILURE_TRIES
    ) -> None:
        self._m3u8_url = m3u8_url

        if not os.path.exists(video_path):
            os.mkdir(video_path)

        if any([ch in video_name for ch in FILE_SC]):
            raise ValueError("Invalid file name")

        self._video_path = video_path + "//" if not video_path.endswith("//") else ''
        self._video_name = video_name + video_name_extension

        self._params = params
        self._cookies = cookies
        self._headers = headers
        self._proxy = proxy

        self._AUTO_HIGHEST_BANDWIDTH = auto_highest_bandwidth

        self._async_tasks_maintain = async_tasks_maintain if async_tasks_maintain > 0 else ASYNC_TASKS_MAINTAIN
        self._inspect_interval = inspect_interval if inspect_interval > 0 else INSPECT_INTERVAL
        self._failure_retries = failure_retries if failure_retries > 0 else FETCH_FAILURE_TRIES

        self._progress_bar_display = progress_bar_display
        self._decrypt_key = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    async def download(self) -> None:
        m3u8_url_seq = await self._specify_stream()
        await self._fetch_seq_slices(m3u8_url_seq)

        self._progress_bar.close()
        self._merge.start()

    async def _specify_stream(self) -> str:
        """ specify an adaptation stream """

        if all(ret_val := Parse.url(self._m3u8_url)):
            self._host_url = ret_val[0][0][: -1]
            self._prefix_url = ret_val[1][0][: -1]
        else:
            raise ValueError("Invalid m3u8 addr")

        async with aiohttp.ClientSession() as session:
            resp = await _get(session, self._m3u8_url, self._failure_retries, params=self._params,
                              cookies=self._cookies, headers=self._headers, proxy=self._proxy)

            if not resp or resp.status != 200:
                raise Exception("m3u8 url is not available")

            resp_text = await resp.text()
            if len(ret := Parse.fetch_multi_rate_adaptation(resp_text)):
                # multi-rate adaptation stream

                _b = int(ret[0][0])
                _u = ret[0][1]
                for (index, (bandwidth, resource_addr)) in enumerate(ret):
                    if self._AUTO_HIGHEST_BANDWIDTH:
                        if _b < int(bandwidth):
                            _b = int(bandwidth)
                            _u = resource_addr
                    else:
                        print(f"{index + 1} - bandwidth[{bandwidth}]")

                if self._AUTO_HIGHEST_BANDWIDTH:
                    # quality stream picked automatically
                    return (self._host_url if _u[0] == '/' else self._prefix_url) + _u
                else:
                    print("Select a specific quality video stream from above, `0` for quit")
                    while True:
                        _c = int(input("choice: "))

                        if not _c:
                            exit(EXIT_MIDWAY)
                        elif 0 < _c <= len(ret):
                            return (self._host_url if ret[_c-1][1][0] == '/' else self._prefix_url) + ret[_c-1][1]

            elif len(Parse.fetch_media_sequential_slices(resp_text)):
                return self._m3u8_url
            else:
                raise Exception("Unresolved m3u8 content")

    async def _fetch_seq_slices(
        self, m3u8_url_seq: str
    ) -> None:
        """ fetch all stream slices in current m3u8 file """

        if all(ret_val := Parse.url(m3u8_url_seq)):
            self._host_url = ret_val[0][0][: -1]
            self._prefix_url = ret_val[1][0]
        else:
            raise ValueError("Invalid m3u8 addr")

        async with aiohttp.ClientSession() as session:
            resp = await _get(session, m3u8_url_seq, self._failure_retries, params=self._params,
                              cookies=self._cookies, headers=self._headers, proxy=self._proxy)

            if not resp or resp.status != 200:
                raise Exception("m3u8 url sequences is not available")

            text = await resp.text()

            slices = Parse.fetch_media_sequential_slices(text)
            if not slices:
                raise Exception("Unresolved m3u8 content")

            await self._fetch_decrypt_key(session, Parse.key(text))

            # Note: init video uri has been added into slices list if it has
            self._merge = Merge(text, self._video_path, self._video_name, slices)
            self._progress_bar = tqdm(total=len(slices),
                                      desc="Downloading",
                                      ncols=100) if self._progress_bar_display else None

            if not slices[0].startswith("http"):
                _ = self._host_url if slices[0][0] == '/' else self._prefix_url
                slices = [_ + slice_ for slice_ in slices]

            self._slices_urls_manager(init=True, urls=slices)

            self._failure_tries_count = 0
            _slices_urls_init_size = self._slices_urls.qsize()
            while True:
                # calculate the number of adding async tasks in this round
                supply_num = (_slices_urls_init_size
                              if self._async_tasks_maintain == ASYNC_TASKS_MAINTAIN else
                              self._async_tasks_maintain) + MAIN_ASYNC_TASK_SYMBOL - len(asyncio.all_tasks())

                if supply_num:
                    urls_batch = self._slices_urls_manager(init=False, gain=supply_num)

                    if not urls_batch and len(self._slices_urls_failure):
                        if self._failure_tries_count < self._failure_retries:
                            # redo failure tasks
                            self._failure_tries_count += 1
                            urls_batch = self._slices_urls_failure.copy()
                        else:
                            raise Exception("part of slices can not be downloaded, "
                                            "or try to increase the number of `failure_retries` argument")

                    # async tasks payload
                    tasks = [
                        asyncio.create_task(self._fetch_single_slice(session, url), name=url)
                        for url in urls_batch
                    ]

                    for task in tasks:
                        task.add_done_callback(functools.partial(self._task_done_callback))

                    # keep from fetching the failed slices that have no results yet
                    self._slices_urls_failure.clear()

                # yield from current main process to handle slices tasks
                await asyncio.sleep(self._inspect_interval)

                if self._slices_total_num == self._slices_done_count:
                    break

    async def _fetch_single_slice(
        self, session: aiohttp.ClientSession, url: str
    ) -> bool:
        """ single slice download coroutine """

        try:
            resp = await _get(session, url, self._failure_retries, params=self._params,
                              cookies=self._cookies, headers=self._headers, proxy=self._proxy)
            if not resp:
                return False

            file_name = url[url.rfind('/') + 1:]

            if self._merge.is_slices_replace:
                # replace file name in reflection list provided by `Merge`
                file_name = self._merge.slices_replace_reflection[url]

            with open(os.path.join(self._video_path, file_name), 'wb') as slice_file:
                _content = await resp.read()
                slice_file.write(self._decrypt_key.decrypt(_content) if self._decrypt_key else _content)
        except (ClientError, TimeoutError):
            return False

        return True

    async def _fetch_decrypt_key(self, session, key_):
        if not key_:
            return

        key_method = key_[0][0]
        key_url = key_[0][1]

        if key_method != "AES-128":
            raise Exception("unresolved encryption method")

        if not key_url.startswith("http"):
            key_url = (self._host_url if key_url[0] == '/' else self._prefix_url) + key_url

        resp = await _get(session, key_url, self._failure_retries, params=self._params,
                          cookies=self._cookies, headers=self._headers, proxy=self._proxy)

        if not resp or resp.status != 200:
            raise Exception("unavailable encryption key url")

        key_text = await resp.read()
        self._decrypt_key = AES.new(key_text, AES.MODE_CBC)

    def _slices_urls_manager(
        self, *, init: bool, urls: Optional[list] = None, gain: Optional[int] = 0
    ) -> Union[None, list]:
        """
            continuously return a group of urls that should be handled as async tasks
            OR
            build up a queue that contain all urls
        """

        if init:
            if not urls:
                raise ValueError("`urls` must not be empty while `init` is positive")

            # build up
            self._slices_total_num = len(urls)
            self._slices_done_count = 0

            self._slices_urls = SimpleQueue()
            self._slices_urls_failure = []

            for url in urls:
                self._slices_urls.put(url)
        else:
            # reap
            rets = []

            if gain > 0:
                for i in range(gain):
                    if not self._slices_urls.qsize():
                        break

                    rets.append(self._slices_urls.get())

            return rets

    def _task_done_callback(self, task: Task) -> None:
        """ task callback """

        _name = task.get_name()

        if task.result():
            self._slices_done_count += 1
            self._failure_tries_count = self._failure_tries_count - 1 if self._failure_tries_count > 0 else 0

            if self._progress_bar_display:
                self._progress_bar.update(1)
        else:
            self._slices_urls_failure.append(_name)
