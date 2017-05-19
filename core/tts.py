import os
import string
import subprocess
from urllib.parse import quote

from util.config import Config
from util.utils import HttpUtils


class TextToSpeech:
    @classmethod
    def convert(cls, text, audio_file_path):
        url = 'http://tts.baidu.com/text2audio?idx=1&tex=%s&cuid=baidu_speech_demo&cod=2&lan=zh&ctp=1&pdt=1&spd=5&per=0&vol=5&pit=5' % text
        url = quote(url, safe=string.printable)
        HttpUtils.download_file(url, audio_file_path)

    @classmethod
    def convert_and_play(cls, text):
        audio_file_path = os.path.join(Config.get("u_path"), "tts.mp3")
        # remove existing file
        if os.path.isfile(audio_file_path):
            os.remove(audio_file_path)

        # download
        cls.convert(text, audio_file_path)

        # play
        subprocess.call(["mplayer", audio_file_path])


if __name__ == "__main__":
    TextToSpeech.convert("This is a test for tts", "tts.mp3")
