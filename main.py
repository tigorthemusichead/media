from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import wave
import json
from pydub import AudioSegment

file_name = input("Enter the input audio filename: ")
given_audio = given_audio = AudioSegment.from_file(file_name, format=file_name[file_name.find('.')+1:])
given_audio = given_audio.set_channels(1)
given_audio.export("audio.wav", format="wav")

text_name = input("Enter the output text file name: ")

SetLogLevel(0)

wf = wave.open("audio.wav", "rb")
text = open(text_name, "w")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print ("Audio file must be WAV format mono PCM.")
    exit (1)

model = Model("model")
rec = KaldiRecognizer(model, wf.getframerate())
rec.SetWords(True)
rec.SetPartialWords(True)
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        text.write(json.loads(rec.Result())["text"], end='\n')