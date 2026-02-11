#!/usr/bin/env python3

import sounddevice as sd
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import sys

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
NUM_BARS = 20
SMOOTHING = 0.7

bar_heights = np.zeros(NUM_BARS)

def find_device(name_keyword):
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if name_keyword.lower() in device['name'].lower():
            return i
    return None

def audio_callback(indata, frames, time, status):
    global bar_heights
    if status:
        print(status)

    audio_data = indata[:, 0]
    fft_data = np.fft.rfft(audio_data)
    fft_magnitude = np.abs(fft_data)

    freq_bins = len(fft_magnitude)
    log_indices = np.logspace(np.log10(1), np.log10(freq_bins), NUM_BARS + 1, dtype=int)
    new_heights = []
    for i in range(NUM_BARS):
        start = log_indices[i]
        end = log_indices[i + 1]
        if start < end:
            new_heights.append(np.mean(fft_magnitude[start:end]))
        else:
            new_heights.append(0)

    bar_heights = np.array(new_heights)

device_id = find_device("CABLE Output")
stream = sd.InputStream(callback=audio_callback, device=device_id, channels=2, samplerate=SAMPLE_RATE, blocksize=CHUNK_SIZE)
stream.start()

app = QApplication(sys.argv)

win = pg.plot(title="Audio Visualizer")
win.setYRange(0, 500)
win.setXRange(0, NUM_BARS)

bar_graph = pg.BarGraphItem(x=range(NUM_BARS), height=bar_heights, width=0.8, brush='b')
win.addItem(bar_graph)

def update():
    global bar_heights
    current_heights = bar_graph.opts['height']
    target_heights = bar_heights
    smoothed_heights = current_heights * SMOOTHING + target_heights * (1 - SMOOTHING)
    bar_graph.setOpts(height=smoothed_heights)

timer = QTimer()
timer.timeout.connect(update)
timer.start(50)

sys.exit(app.exec())