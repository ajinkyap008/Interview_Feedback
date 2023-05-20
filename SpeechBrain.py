import whisper
import datetime

import subprocess

import torch
import pyannote.audio
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding

from pyannote.audio import Audio
from pyannote.core import Segment

import wave
import contextlib

from sklearn.cluster import AgglomerativeClustering
import numpy as np

import moviepy.editor as mp

import os

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def convert_to_audio(video_path):
  video = mp.VideoFileClip(video_path)
  if not os.path.exists("./audio_files/"):
    os.makedirs("./audio_files/")
  video.audio.write_audiofile("./audio_files/interviewAudio.mp3")

num_speakers = 2
language = 'English'
model_size = 'base'
path = "./audio_files/interviewAudio.mp3"

model_name = model_size
if language == 'English' and model_size != 'large':
  model_name += '.en'

embedding_model = PretrainedSpeakerEmbedding( 
    "speechbrain/spkrec-ecapa-voxceleb",
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu"))

def segment_embedding(segment, duration, audio, path):
  start = segment["start"]
  end = min(duration, segment["end"])
  clip = Segment(start, end)
  waveform, sample_rate = audio.crop(path, clip)
  return embedding_model(waveform[None])

def time(secs):
  return datetime.timedelta(seconds=round(secs))

def write_result(segments):
  f = open("InterviewTranscript.txt", "w")
  for (i, segment) in enumerate(segments):
    if i == 0 or segments[i - 1]["speaker"] != segment["speaker"]:
      f.write("\n" + segment["speaker"] + ' ' + str(time(segment["start"])) + '\n')
    f.write(segment["text"][1:] + ' ')
  f.close()

def start_diarization(path):
  if path[-3:] != 'wav':
    subprocess.call(['ffmpeg', '-i', path, 'audio.wav', '-y'])
    path = 'audio.wav'

  model = whisper.load_model(model_size)

  result = model.transcribe(path)
  segments = result["segments"]

  with contextlib.closing(wave.open(path,'r')) as f:
    frames = f.getnframes()
    rate = f.getframerate()
    duration = frames / float(rate)

  audio = Audio()

  embeddings = np.zeros(shape=(len(segments), 192))
  for i, segment in enumerate(segments):
    embeddings[i] = segment_embedding(segment, duration, audio, path)

  embeddings = np.nan_to_num(embeddings)

  clustering = AgglomerativeClustering(num_speakers).fit(embeddings)
  labels = clustering.labels_
  for i in range(len(segments)):
    segments[i]["speaker"] = 'SPEAKER ' + str(labels[i] + 1)

  write_result(segments)

def do_script(path_input):
  convert_to_audio(path_input)
  start_diarization(path)