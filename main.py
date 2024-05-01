import asyncio
from bilibili_api import video, Credential, HEADERS, sync
import httpx
import os
import time
import json
import re

from player import MusicPlayer

with open('save.json', 'r', encoding='utf-8') as f:
    saves = json.load(f)
print(saves)


mgr = MusicPlayer()

current = None
memory = []
player = None

SAVE_BV = 'save/BV/'
SAVE_BV = os.path.abspath(SAVE_BV) + '\\'

SESSDATA = "3bc7973f%2C1718889962%2C9a57a%2Ac2CjDYJpIB5LEY4mNnx-fHTFs8kGdQ37pA-m4eMlgRDB3M5DobbPwP3apofDd75_OQm0oSVjA1REhhTXR2WDU2TXVzeWJCOUZUNFJxT1hQZGctbk8wZ2N1NTdRc1YxbTRyX0ExWHBlYTlJeFdnZDVaVHVEaHN2eXlQRjRuYVRXRVNEZmkzdDZvSWxBIIEC"
BILI_JCT = "7aea6b497e5da8d2a3004483bcd6b35a"
BUVID3 = "A78DB65F-603D-EAC7-C204-3D336E059A9F66669infoc"

credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)


class Song:
    def __init__(self, aid=None, bvid=None):
        self.video = video.Video(aid=aid, bvid=bvid, credential=credential)
        self.info = sync(self.video.get_info())
        self.saved = self.video.get_bvid() in saves

    def download_video(self):
        pass

    def download_song(self):
        bv_id = self.video.get_bvid()
        pic = self.info['pic']
        download_url_data = sync(self.video.get_download_url(0))
        detector = video.VideoDownloadURLDataDetecter(data=download_url_data)
        streams = detector.detect_best_streams()

        if detector.check_flv_stream():
            sync(download_url(streams[0].url, "flv_temp.flv"))
            os.system(f'ffmpeg -i input.flv -vn -c:a libmp3lame {SAVE_BV}{bv_id}.mp3')
            os.remove("flv_temp.flv")
        else:
            sync(download_url(streams[1].url, "audio_temp.m4s"))
            os.system(f'ffmpeg -i audio_temp.m4s -vn -c:a libmp3lame -q:a 1 {SAVE_BV}{bv_id}.mp3')
            os.remove("audio_temp.m4s")
        sync(download_url(pic, f'{SAVE_BV}{bv_id}.jpg'))
        self.saved = True

    def show_info(self):
        for i in self.info.keys():
            print('KEY: ', i)
            print('ITEM: ', self.info[i])
            print('\r\n')


async def download_url(url: str, out: str):
    async with httpx.AsyncClient(headers=HEADERS) as sess:
        resp = await sess.get(url)
        length = resp.headers.get('content-length')
        with open(out, 'wb') as f:
            process = 0
            for chunk in resp.iter_bytes(1024):
                if not chunk:
                    break

                process += len(chunk)
                f.write(chunk)


def show_song_info(song):
    info = sync(song.get_info())
    print(info['pic'])
    print(info['title'])
    print(info['desc'])
    print(info['duration'])


if __name__ == '__main__':
    print('输入help以查看帮助')
    while True:
        action = input('>>>')

        if action == 'exit':
            if current is not None:
                current = None
            else:
                print('退出程序')
                break

        elif action == 'show':
            if isinstance(current, Song):
                current.show_info()
            else:
                print('unsupported type')
                print(type(current))

        elif action == 'download':
            if isinstance(current, Song):
                if not current.saved:
                    current.download_song()
                    saves[current.video.get_bvid()] = current.info
                    with open('save.json', 'w', encoding='utf-8') as f:
                        json.dump(saves, f)
                else:
                    print('已下载')

        elif action == 'help':
            print("""
            没有help，自己看代码
            """)

        elif action == 'play':
            if isinstance(current, Song):
                if current.saved:
                    mgr.load(f'{SAVE_BV}{current.video.get_bvid()}.mp3')
            else:
                mgr.PlayChange()

        elif action == 'stop':
            mgr.PlayChange()
        
        else:
            action = action.split()
            if not action:
                pass
            elif action[0] == 'play':
                if mgr.IsPlayed():
                    if action[1] == 'modeC':
                        print(mgr.change_play_mode())
                    if len(action) == 3:
                        time = int(action[2])
                        if action[1] == '<':
                            mgr.forward()
                        elif action[1] == '>':
                            mgr.rewind()

            elif action[0] == 'search':
                if len(action) == 3:
                    if action[1] == 'av':
                        current = Song(aid=action[2])
                        print(current.info['title'])
                    elif action[1] == 'bv':
                        current = Song(bvid=action[2])
                        print(current.info['title'])
                    elif action[1] == 'url':
                        bvid = re.findall("BV[a-zA-Z0-9]{10}", action[2])
                        if len(bvid):
                            current = Song(bvid=bvid[0])
                            print(current.info['title'])
                        else:
                            print('error: 该url不包含有效BV号')
        

