from typing import List, Optional, Union

import numpy as np
import sounddevice as sd
from kokoro import KPipeline


class KokoroTTS:
    lang_map = {
        "us": "a",  # American English
        "uk": "b",  # British English
        "es": "e",  # Spanish
        "fr": "f",  # French
        "hi": "h",  # Hindi
        "it": "i",  # Italian
        "jp": "j",  # Japanese
        "pt": "p",  # Brazilian Portuguese
        "zh": "z",  # Mandarin Chinese
    }

    default_voice_map = {
        "us": "am_michael",
        "uk": "bm_george",
        "es": "af_sky",
        "fr": "af_nicole",
        "hi": "af_sarah",
        "it": "bf_emma",
        "jp": "af_bella",
        "pt": "bf_isabella",
        "zh": "am_adam",
    }

    def __init__(
        self,
        lang: Optional[str] = "us",
        voice: Optional[str] = "af_heart",
        sample_rate: Optional[int] = 24000,
    ):
        self.lang_code = lang
        self.lang = self.lang_map[lang]
        self.voice = voice if voice else self.default_voice_map[lang]
        self.sample_rate = sample_rate

        self.pipeline = None

    def _init_kokoro_tts(self, lang: Optional[str] = None) -> None:
        lang_code = self.lang
        if lang:
            lang_code = self.lang_map.get(lang, self.lang)

        self.pipeline = KPipeline(lang_code=lang_code)

    def create_smaller_chunks(self, text, chunk_size):
        text = text.replace("*", "")
        text = text.replace("\n", " ").strip()
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            if end < len(text):
                last_period = text.rfind(". ", start, end)
                last_question = text.rfind("? ", start, end)
                last_exclaim = text.rfind("! ", start, end)

                break_point = max(last_period, last_question, last_exclaim)

                if break_point != -1 and break_point > start:
                    end = break_point + 2
                else:
                    last_space = text.rfind(" ", start, end)
                    if last_space != -1 and last_space > start:
                        end = last_space + 1
                    else:
                        end = min(start + chunk_size, len(text))
            else:
                end = len(text)

            chunk = text[start:end].strip()
            chunks.append(chunk)
            start = end

        return chunks

    def play_audio(
        self,
        text: str,
        lang: str,
        voice: str,
        speed: float = 1.0,
        chunk_size: int = 200,
    ):
        if self.pipeline is None:
            self._init_kokoro_tts(lang)
        elif lang and self.lang != self.lang_map.get(lang):
            self.lang = self.lang_map.get(lang, self.lang)
            self._init_kokoro_tts(lang)

        if voice:
            self.voice = voice

        audio_chunks = []

        chunks = self.create_smaller_chunks(text, chunk_size)

        for i, chunk in enumerate(chunks, 1):
            generator = self.pipeline(chunk, speed=speed, voice=self.voice)

            for gs, ps, audio in generator:
                audio_chunks.append(audio)

        audio = np.concatenate(audio_chunks)
        sd.play(audio, self.sample_rate)
        sd.wait()
