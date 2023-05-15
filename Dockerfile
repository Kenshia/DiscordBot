FROM python:3.10
WORKDIR /app
COPY ai_memory.py ai_module.py discord_bot.py utility.py requirements.txt LICENSE /app/
RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN apt-get update && apt-get install -y espeak ffmpeg
CMD ["python", "main.py"]