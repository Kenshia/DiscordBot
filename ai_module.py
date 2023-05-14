# from discord.ext import voice_recv
import speech_recognition as sr
import pyttsx3
import os
import time
import wave
import requests
import soundfile as sf
import numpy as np
from scipy.signal import resample_poly
from dotenv import load_dotenv
from ai_memory import AiMemory

load_dotenv()
recognizer = sr.Recognizer()
memory = AiMemory()


def get_voice_from_text(command) -> bytes:
    _name = time.time()
    _engine = pyttsx3.init()
    _engine.save_to_file(command, f'{_name}.wav')
    _engine.runAndWait()

    __fix_data(f'{_name}.wav')
    result = None

    with wave.open(f'{_name}.wav', 'rb') as file:
        result = file.readframes(-1)

    os.remove(f'{_name}.wav')
    return result


def __fix_data(input_file):
    # load the input file
    data, samplerate = sf.read(input_file)

    # resample to 44100 Hz
    data = resample_poly(data, 44100, samplerate)

    # convert to stereo
    if len(data.shape) == 1:
        data = np.column_stack((data, data))

    os.remove(input_file)
    sf.write(input_file, data, samplerate=44100, subtype='PCM_16')


def _get_text_from_audio(audio):
    try:
        text = recognizer.recognize_google(audio)
        text = text.lower()
        return text
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
    except sr.UnknownValueError:
        print("unknown error occurred")


def __get_response_from_text_gpt_via_rapidapi(text, conversation_id):
    url = "https://chatgpt-gpt-3-5.p.rapidapi.com/ask"

    text = memory.add_history(text, 'Human', conversation_id)
    payload = {"query": text}

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": os.getenv('X_RAPIDAPI_KEY'),  # personal key
        "X-RapidAPI-Host": "chatgpt-gpt-3-5.p.rapidapi.com"
    }

    response = requests.post(url, json=payload, headers=headers)
    memory.add_history(response.json()['response'], 'AI', conversation_id)

    return response.json()['response']


def response_from_text(text: str, conversation_id: int):
    response = __get_response_from_text_gpt_via_rapidapi(text, conversation_id)
    return response

# ABANDONED VOICE RECOGNITION CODE
# class VoiceRecognizerThread:
#     empty_bytes = b'\xf8\xff\xfe'

#     def _process(self):
#         print('Processing audio...')

#         decoded = []
#         decoder = discord.opus.Decoder()

#         for chunk in self.buffer:
#             opus_data = b'|' + chunk
#             decoded_chunk = decoder.decode(opus_data)
#             decoded.append(decoded_chunk)
#         decoded = b''.join(decoded)

#         # create a WAV file in memory
#         with io.BytesIO() as wav_file:
#             with wave.open(wav_file, 'wb') as wav:
#                 wav.setnchannels(2)
#                 wav.setsampwidth(2)
#                 wav.setframerate(48000)
#                 wav.writeframes(decoded)
#             # get the WAV file data as bytes
#             wav_bytes = wav_file.getvalue()

#             # write to disk
#             with open(f'output.wav', 'wb') as f:
#                 f.write(wav_bytes)

#         ####################################
#         # text = _get_text_from_audio(audio)

#         # if text is not None:
#         #     print('VoiceRecognizerThread: ' + text)
#         #     if self.callback is not None:
#         #         self.callback(text)  # call callback function

#     def incoming_packet(self, packet: voice_recv.rtp.RTPPacket):
#         if packet.decrypted_data == self.empty_bytes:
#             self.empty_data_streak += 1
#             if self.empty_data_streak >= 10 & len(self.buffer) > 0:
#                 self.empty_data_streak = 0
#                 self._process()
#                 self.buffer = []
#         else:
#             opus_data = packet.decrypted_data
#             self.buffer.append(opus_data)

#     def __init__(self):
#         self.buffer = []
#         self.empty_data_streak = 0
#         self.callback = None

#         self.nchannel = 2  # discord is stereo
#         self.sample_width = 2  # 16-bit audio
#         self.sample_rate = 48000  # default discord opus audio sample rate
#         self.speech_recognition_sample_rate = self.sample_rate * \
#             self.nchannel  # sr must be mono -> stereo * nchannel

#         print('VoiceRecognizerThread started')

#     def __del__(self):
#         print('VoiceRecognizerThread closed')

#     def set_callback(self, callback):
#         self.callback = callback
