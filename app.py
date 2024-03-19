import datetime
import os
import wave
import json
import time
from vosk import Model, KaldiRecognizer, SetLogLevel
from flask import Flask, request, abort, render_template
from pydub import AudioSegment
from werkzeug.utils import secure_filename

app = Flask(__name__)


def process_file(file_name):
  given_audio = AudioSegment.from_file(file_name, format=file_name[-3:])
  given_audio = given_audio.set_channels(1)
  given_audio.export(f"{file_name[:-4]}.wav", format="wav")
  SetLogLevel(0)

  wf = wave.open(f"{file_name[:-4]}.wav", "rb")
  file = open(f"{file_name[:-4]}.txt", "w")
  if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("Audio file must be WAV format mono PCM.")
    exit(1)

  model = Model("model")
  rec = KaldiRecognizer(model, wf.getframerate())
  rec.SetWords(True)
  rec.SetPartialWords(True)
  while True:
    data = wf.readframes(4000)
    if len(data) == 0:
      break
    if rec.AcceptWaveform(data):
      file.write(json.loads(rec.Result())["text"] + "\n\n")
  file.close()
  os.remove(f"{file_name[:-4]}.wav")
  os.remove(file_name)

  file = open(f"{file_name[:-4]}.txt", "r")
  text = file.read()
  file.close()
  return text
@app.route('/', methods=['GET', 'POST'])
def home():
  if request.method == 'GET':
    return render_template('base.html')
  if request.method == 'POST':
    file = request.files['file']
    file_name = f"./uploaded/{time.time()}_{secure_filename(file.filename)}"
    file.save(file_name)
    text = process_file(file_name)
    return render_template('base.html', text=text)
  else:
    abort(400)


if __name__ == "__main__":
  app.run(debug=False)
