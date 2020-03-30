import os
import string
import subprocess
import sys
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
        audio_file_path = os.path.join(Config.get("tts_path"), "tts-%s.mp3" % hash(text))

        if not os.path.isfile(audio_file_path):
            # if not exist, download
            cls.convert(text, audio_file_path)

        # play
        subprocess.call(["mpv", audio_file_path])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit()
    TextToSpeech.convert_and_play(sys.argv[1])
