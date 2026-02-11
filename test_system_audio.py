#!/usr/bin/env python3

import sounddevice as sd
import sys
from PyQt6.QtWidgets import QApplication
from visualizer import AudioVisualizer

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024

def find_device(name_keyword):
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if name_keyword.lower() in device['name'].lower():
            return i
    return None

app = QApplication(sys.argv)
visualizer = AudioVisualizer(num_bars=20, smoothing=0.7, sample_rate=SAMPLE_RATE)

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    
    audio_data = indata[:, 0]
    visualizer.process_audio(audio_data)

device_id = find_device("CABLE Output")
stream = sd.InputStream(
    callback=audio_callback,
    device=device_id,
    channels=2,
    samplerate=SAMPLE_RATE,
    blocksize=CHUNK_SIZE
)
stream.start()

sys.exit(app.exec())