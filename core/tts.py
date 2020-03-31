import os
import string
import subprocess
import hashlib
from urllib.parse import quote

from util.config import Config
from util.utils import HttpUtils


class TextToSpeech:
    md5 = hashlib.md5()

    @classmethod
    def convert(cls, text, audio_file_path):
        url = 'http://tts.baidu.com/text2audio?idx=1&tex=%s&cuid=baidu_speech_demo&cod=1&lan=zh&ctp=1&pdt=1&spd=4&per=5&vol=5&pit=7' % text
        url = quote(url, safe=string.printable)
        HttpUtils.download_file(url, audio_file_path, over_write=True)

    @classmethod
    def convert_and_play(cls, text):
        cls.md5.update(text.encode("utf-8"))
        audio_file_path = os.path.join(Config.get("tts_path"), "tts-%s.mp3" % cls.md5.hexdigest())
        print(audio_file_path)

        cls.convert(text, audio_file_path)

        # play
        subprocess.call(["mpv", audio_file_path])


if __name__ == "__main__":
    TextToSpeech.convert_and_play("小朋友，你好，今天去哪里玩了")
