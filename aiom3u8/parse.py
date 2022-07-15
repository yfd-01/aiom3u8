# -*- coding: utf-8 -*-
import re

format_rules = {
    "URL_HOST": re.compile(r"^https?://.*?/"),
    "URL_PREFIX": re.compile(r"^https?://.*/"),
    "MULTI_RATE": re.compile(r"BANDWIDTH=(\d*).*\n(.*\.m3u8.*)"),
    "MEDIA_SEQ": re.compile(r"#EXTINF:.*,\n(.*)\n"),
    "CRYPT_KEY": re.compile(r'#EXT-X-KEY:METHOD=(.*),URI="(.*)"\n')
}


class Parse:
    @staticmethod
    def fetch_multi_rate_adaptation(file_content):
        return format_rules["MULTI_RATE"].findall(file_content)

    @staticmethod
    def fetch_media_sequential_slices(file_content):
        return format_rules["MEDIA_SEQ"].findall(file_content)

    @staticmethod
    def url(url):
        return format_rules["URL_HOST"].findall(url), format_rules["URL_PREFIX"].findall(url)

    @staticmethod
    def key(file_content):
        return format_rules["CRYPT_KEY"].findall(file_content)
