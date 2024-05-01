import asyncio
from bilibili_api import video, Credential, HEADERS, sync
import httpx
import os
import time

save_dir = '/save/BV'
print()

SESSDATA = "3bc7973f%2C1718889962%2C9a57a%2Ac2CjDYJpIB5LEY4mNnx-fHTFs8kGdQ37pA-m4eMlgRDB3M5DobbPwP3apofDd75_OQm0oSVjA1REhhTXR2WDU2TXVzeWJCOUZUNFJxT1hQZGctbk8wZ2N1NTdRc1YxbTRyX0ExWHBlYTlJeFdnZDVaVHVEaHN2eXlQRjRuYVRXRVNEZmkzdDZvSWxBIIEC"
BILI_JCT = "7aea6b497e5da8d2a3004483bcd6b35a"
BUVID3 = "A78DB65F-603D-EAC7-C204-3D336E059A9F66669infoc"

credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)

# FFMPEG 路径
FFMPEG_PATH = "ffmpeg"


async def download_url(url: str, out: str, info: str):
    # 下载函数
    async with httpx.AsyncClient(headers=HEADERS) as sess:
        resp = await sess.get(url)
        length = resp.headers.get('content-length')
        with open(out, 'wb') as f:
            process = 0
            for chunk in resp.iter_bytes(1024):
                if not chunk:
                    break

                process += len(chunk)
                print(f'下载 {info} {process} / {length}')
                f.write(chunk)

async def get_video_info(bv_id=None):
    v = video.Video(bvid="BV1zv411G79U", credential=credential)
    info = await v.get_info()
    # print(info['pic'])
    # print(info['title'])
    # print(info['desc'])
    # print(info['duration'])
    # print(info)
    for i in info.keys():
        print('KEY: ', i)
        print('ITEM: ', info[i])
        print('\r\n\r\n')



async def music_download(bv_id=None):
    v = video.Video(bvid="BV1zv411G79U", credential=credential)
    # 获取视频下载链接
    download_url_data = await v.get_download_url(0)
    # 解析视频下载信息
    detector = video.VideoDownloadURLDataDetecter(data=download_url_data)
    streams = detector.detect_best_streams()

    info = await v.get_info()
    print(info['pic'])
    print(info['title'])
    print(info['desc'])
    print(info['duration'])

    # 有 MP4 流 / FLV 流两种可能
    if detector.check_flv_stream():
        # FLV 流下载
        await download_url(streams[0].url, "flv_temp.flv", "FLV 音视频流")
        # 转换文件格式
        os.system(f'ffmpeg -i input.flv -vn -c:a libmp3lame output.mp3')
        # 删除临时文件
        os.remove("flv_temp.flv")
    else:
        await download_url(streams[1].url, "audio_temp.m4s", "音频流")


if __name__ == '__main__':
    # 测试
    bv_id = 'BV1zv411G79U'
    sync(get_video_info())
