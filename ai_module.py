import speech_recognition as sr
import pyttsx3
import os
from dotenv import load_dotenv
from ai_memory import AiMemory

load_dotenv()
recognizer = sr.Recognizer()
memory = AiMemory()


def speak_text(command):
    engine = pyttsx3.init()
    engine.say(command)
    engine.runAndWait()


def __get_audio_file_from_text(text):
    raise Exception("not implemented")


def __get_text_from_audio_filepath(filepath):
    try:
        with sr.AudioFile(filepath) as source:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            text = text.lower()
            return text
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
    except sr.UnknownValueError:
        print("unknown error occurred")


def __get_response_from_text_gpt(text):
    try:
        import openai
    except ImportError:
        raise AttributeError("Could not find openai; check installation")

    openai.api_key = os.getenv('OPENAI_API_KEY')

    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt=text,
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        stop=["\n", " Human:", " AI:"]
    )
    return response.choices[0].text


def __get_response_from_text_gpt_via_rapidapi(text, conversation_id):
    try:
        import requests
    except ImportError:
        raise AttributeError("Could not find requests; check installation")

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


def __get_response_from_text(text, conversation_id):
    return __get_response_from_text_gpt_via_rapidapi(text, conversation_id)


# def response_from_audio_filepath(audio_filepath: str):
#     text = __get_text_from_audio_filepath(audio_filepath)
#     response, conversation_id = __get_response_from_text(text)
#     return response, conversation_id


def response_from_text(text: str, conversation_id: int):
    response = __get_response_from_text(text, conversation_id)
    return response
