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
    log_indices = np.logspace(np.log10(2), np.log10(freq_bins), NUM_BARS, dtype=int)
    log_indices = np.concatenate(([0], log_indices))

    for i in range(1, len(log_indices)):
        if log_indices[i] <= log_indices[i-1]:
            log_indices[i] = log_indices[i-1] + 1

    new_heights = []
    for i in range(NUM_BARS):
        start = log_indices[i]
        end = log_indices[i + 1]
        if start < end and end <= freq_bins:
            avg = np.mean(fft_magnitude[start:end])
            boost = 0.3 + (i / NUM_BARS) * 20
            new_heights.append(avg * boost)
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
win.setBackground('k')
win.hideAxis('left')
win.hideAxis('bottom')
win.showGrid(x=False, y=False)

colors = []
for i in range(NUM_BARS):
    ratio = i / NUM_BARS
    if ratio < 0.25:
        r = 0
        g = int(200 + 55 * (ratio / 0.25))
        b = int(255 * (ratio / 0.25))
    elif ratio < 0.5:
        r = 0
        g = int(255 * (1 - (ratio - 0.25) / 0.25))
        b = 255
    elif ratio < 0.75:
        r = int(255 * ((ratio - 0.5) / 0.25))
        g = 0
        b = 255
    else:
        r = int(255 * (1 - (ratio - 0.75) / 0.25) * 0.6 + 128)
        g = 0
        b = 255
    
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    
    colors.append((r, g, b))

bar_graph = pg.BarGraphItem(x=range(NUM_BARS), height=bar_heights, width=0.8, brushes=colors)
win.addItem(bar_graph)

def update():
    global bar_heights
    current_heights = bar_graph.opts['height']
    target_heights = bar_heights * 2
    smoothed_heights = current_heights * SMOOTHING + target_heights * (1 - SMOOTHING)
    bar_graph.setOpts(height=smoothed_heights)

timer = QTimer()
timer.timeout.connect(update)
timer.start(50)

sys.exit(app.exec())