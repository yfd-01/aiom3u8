# aiom3u8
解析m3u8文件进行视频文件的异步下载

## 下载安装
```python
$ python -m pip install aiom3u8

# 镜像加速
$ python -m pip install aiom3u8 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 基本用法:

```python
import aiom3u8

aiom3u8.download("https://demo.com/demo/demo.m3u8", "C:\\video_path", "video_name")  # 使用默认参数

params = {...}
cookies = {...}
headers = {...}
aiom3u8.download("https://demo.com/demo/demo.m3u8", "C:\\video_path", "video_name",  # 使用调节参数 
                  video_name_extension=".mp4", params=params, cookies=cookies, headers=headers, proxy="http://127.0.0.1:10809/"
                  auto_highest_bandwidth=True, progress_bar_display=True, async_tasks_maintain=20, inspect_interval=3.,
                  failure_retries=5)
```

**OR**

```python
import asyncio
import aiom3u8

async def main():
  await aiom3u8.download_coro(arguments...)
 
asyncio.run(main())
```

## 参数描述:
* ```video_name_extension```:&emsp;&emsp; str &emsp;&emsp;-&emsp;&emsp;生成视频类型
* ```params、cookies、headers```:&nbsp;&nbsp;dict &emsp;&emsp;-&emsp;&emsp;请求时附带参数
* ```proxy```:&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; str &emsp;&emsp;-&emsp;&emsp;自身使用的代理地址
* ```auto_highest_bandwidth```:&emsp; bool &emsp;&emsp;-&emsp;&emsp;有多个适配流时是否自动选择最高画质
* ```progress_bar_display```:&emsp;&emsp; bool &emsp;&emsp;-&emsp;&emsp;是否显示下载进度条
* ```async_tasks_maintain```:&emsp;&emsp; int &emsp;&emsp;-&emsp;&emsp;同时下载的异步任务数
* ```inspect_interval```:&emsp;&emsp;&emsp;&emsp;float &emsp;&emsp;-&emsp;&emsp;添加新异步任务的检查间隔时间
* ```failure_retries```:&emsp;&emsp;&nbsp;&emsp;&emsp; int &emsp;&emsp;-&emsp;&emsp;允许单个文件的下载连接失败次数

<br/>
<hr/>

# aiom3u8
Using async way to download a video file by parsing m3u8 file

## Installing m3u8ToMp4
```python
$ python -m pip install aiom3u8

# Using a mirror
$ python -m pip install aiom3u8 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## Basic Usage:

```python
import aiom3u8

aiom3u8.download("https://demo.com/demo/demo.m3u8", "C:\\video_path", "video_name")  # Using default arguments

params = {...}
cookies = {...}
headers = {...}
aiom3u8.download("https://demo.com/demo/demo.m3u8", "C:\\video_path", "video_name",  # Using adjustment arguments
                  video_name_extension=".mp4", params=params, cookies=cookies, headers=headers, proxy="http://127.0.0.1:10809/"
                  auto_highest_bandwidth=True, progress_bar_display=True, async_tasks_maintain=20, inspect_interval=3.,
                  failure_retries=5)
```

**OR**

```python
import asyncio
import aiom3u8

async def main():
  await aiom3u8.download_coro(arguments...)
 
asyncio.run(main())
```

## Parameter Description:
* ```video_name_extension```:&emsp;&emsp; str &emsp;&emsp;-&emsp;&emsp;generated video type
* ```params、cookies、headers```:&nbsp;&nbsp;dict &emsp;&emsp;-&emsp;&emsp;request with parameters
* ```proxy```:&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; str &emsp;&emsp;-&emsp;&emsp;used proxy address
* ```auto_highest_bandwidth```:&emsp; bool &emsp;&emsp;-&emsp;&emsp;whether to automatically select the highest quality when there are multiple adaptation streams
* ```progress_bar_display```:&emsp;&emsp; bool &emsp;&emsp;-&emsp;&emsp;whether to show the download progress bar
* ```async_tasks_maintain```:&emsp;&emsp; int &emsp;&emsp;-&emsp;&emsp;number of asynchronous tasks running concurrently
* ```inspect_interval```:&emsp;&emsp;&emsp;&emsp;float &emsp;&emsp;-&emsp;&emsp;checking interval for adding new async tasks
* ```failure_retries```:&emsp;&emsp;&nbsp;&emsp;&emsp; int &emsp;&emsp;-&emsp;&emsp;number of download connection failures allowed for a single file
