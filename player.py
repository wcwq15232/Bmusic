import time
from io import BytesIO
import wave
from enum import Enum
from typing import Optional

import pyaudio as pyaudio
from pydub import AudioSegment

OUTPUT_DEVICE = 4  # 自行填写

play_mode = {
    0: '单曲循环',
    1: '播完暂停'
}


class MusicPlayer:
    def __init__(self):
        self.frames: int = 0
        self.audio_processor = MusicProcess()  # 将其他格式的音频统一为wav
        self.play_mode = 0

        # 定义回调函数
        def callback(in_data, frame_count, time_info, status):
            data = self.wf.readframes(frame_count)  # 获取播放数据

            # if self.count >= 10:
            #     play_time = self.wf.tell() // self.rate
            #     print(play_time)
            #     self.count = 0
            # self.count += 1

            if self.wf.tell() + 2 * frame_count > self.frames:
                if self.play_mode == 0:
                    self.wf.setpos(0)
                else:
                    return data, pyaudio.paComplete

            return data, pyaudio.paContinue

        self.callback = callback

        self.p: pyaudio.PyAudio = pyaudio.PyAudio()
        self.wf: Optional[wave.Wave_read] = None
        self.stream: Optional[pyaudio.Stream] = None

        self.rate = 0
        self.count = 0

    def change_play_mode(self):
        self.play_mode = 1 - self.play_mode
        return self.play_mode

    def get_state(self):
        play_time = self.wf.tell() // self.rate

    def load(self, path: str):  # 切换歌曲后重新加载
        # 销毁原wav与stream对象
        if self.stream is not None:
            self.stream.close()
        if self.wf is not None:
            self.wf.close()

        self.wf = self.audio_processor.load_music(path)

        self.rate = self.wf.getframerate()
        self.frames = self.wf.getnframes()

        self.stream = self.p.open(channels=self.wf.getnchannels(),
                                  format=pyaudio.paInt16,
                                  rate=self.wf.getframerate(),
                                  output=True,
                                  stream_callback=self.callback,
                                  output_device_index=OUTPUT_DEVICE)

        self.stream.start_stream()
        print(self.stream.is_active())
        print(self.stream.get_time())

    def play_in_blocking_mode(self, path):
        # 销毁原wav与stream对象
        if self.stream is not None:
            self.stream.close()
        if self.wf is not None:
            self.wf.close()

        self.wf = self.audio_processor.load_music(path)

        self.rate = self.wf.getframerate()
        self.frames = self.wf.getnframes()
        audio = self.p  # 新建一个PyAudio对象
        # wave.open跟python内置的open有点类似，从wf中可以获取音频基本信息
        stream = audio.open(format=pyaudio.paInt16,  # 指定数据类型是int16，也就是一个数据点占2个字节；paInt16=8，paInt32=2，不明其含义，先不管
                            channels=self.wf.getnchannels(),  # 声道数，1或2
                            rate=self.wf.getframerate(),  # 采样率，44100或16000居多
                            frames_per_buffer=1024,  # 每个块包含多少帧，详见下文解释
                            output=True,
                            output_device_index=OUTPUT_DEVICE)
        # getnframes获取整个文件的帧数，readframes读取n帧，两者结合就是读取整个文件所有帧
        stream.write(self.wf.readframes(self.wf.getnframes()))  # 把数据写进流对象
        stream.stop_stream()
        stream.close()
        audio.terminate()

    def __del__(self):
        if self.stream is not None:
            self.stream.close()
        if self.wf is not None:
            self.wf.close()
        self.p.terminate()

    def IsPlayed(self):
        return self.stream.is_active()

    def PlayChange(self):
        # print('c')
        if self.stream.is_active():
            self.stream.stop_stream()
        else:
            self.stream.start_stream()

    def forward(self, seconds=5):  # 快进
        tell = self.wf.tell()
        tell += self.rate * seconds
        if tell > self.frames:
            self.stream.stop_stream()
        else:
            self.wf.setpos(tell)

    def rewind(self, seconds=5):  # 快退
        tell = self.wf.tell()
        tell -= self.rate * seconds
        tell = 0 if tell < 0 else tell
        self.wf.setpos(tell)

    def jump_to(self, sec: int):
        # print(sec)
        # print(self.rate * sec)
        # print(self.frames)
        self.wf.setpos(self.rate * sec)

    def set_volume(self, volume: int):
        if volume != self.audio_processor.volume:
            tell = self.wf.tell()
            flag = False
            if self.stream.is_active():
                self.stream.stop_stream()
                flag = True
            self.wf = self.audio_processor.volume_change(volume)
            self.wf.setpos(tell)
            if flag:
                self.stream.start_stream()


class MusicProcess:
    def __init__(self):
        self.song: Optional[AudioSegment] = None
        self.f = BytesIO()
        self.wav: Optional[wave.Wave_write] = None
        self.volume = 80

    def __form_wav(self):
        if self.wav is not None:
            self.wav.close()
        self.f.seek(0)
        self.wav = wave.open(self.f, 'wb')
        self.wav.setnchannels(self.song.channels)
        self.wav.setsampwidth(self.song.sample_width)
        self.wav.setframerate(self.song.frame_rate)
        self.wav.setnframes(int(self.song.frame_count()))
        self.wav.writeframesraw(self.song._data)
        self.wav.close()
        self.f.seek(0)

    def load_music(self, path: str):
        with open(path, 'rb') as mf:
            self.song = AudioSegment.from_file(mf, format=path.split('.')[-1])

        return self.volume_change(self.volume)

    def volume_change(self, volume):
        self.volume = volume
        self.song = self.song + (volume / 2 - 65) - self.song.dBFS
        self.__form_wav()
        return wave.Wave_read(self.f)


if __name__ == '__main__':
    print('测试程序')
    test_path = r"G:\download\群青讃歌 - Eve MV\3.mp3"
    mgr = MusicPlayer()
    # mgr.play_in_blocking_mode(test_path)
    mgr.load(test_path)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    del mgr
