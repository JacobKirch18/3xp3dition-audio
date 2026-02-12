#!/usr/bin/env python3

import sys
import numpy as np
from PyQt6.QtWidgets import QApplication
from visualizer import AudioVisualizer
import soundfile as sf
import sounddevice as sd

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024

class MediaPlayer:
    def __init__(self, audio_file):
        self.audio_file = audio_file
        self.visualizer = None
        self.stream = None
        self.audio_data = None
        self.position = 0

    def load_audio(self):
        self.audio_data, sr = sf.read(self.audio_file, always_2d=True)
        print(f"Loaded audio file: {self.audio_file}")
        print(f"Sample rate: {sr} Hz")
        print(f"Duration: {len(self.audio_data) / sr:.2f} seconds")

        if self.audio_data.shape[1] > 1:
            self.audio_data_stereo = self.audio_data
            self.audio_data_mono = np.mean(self.audio_data, axis=1)
        else:
            self.audio_data_stereo = np.column_stack([self.audio_data, self.audio_data])
            self.audio_data_mono = self.audio_data.flatten()
    
    def audio_callback(self, outdata, frames, time, status):
        if status:
            print(status)
        
        chunk_stereo = self.audio_data_stereo[self.position:self.position + frames]
        chunk_mono = self.audio_data_mono[self.position:self.position + frames]

        if len(chunk_stereo) < frames:
            chunk_stereo = np.pad(chunk_stereo, ((0, frames - len(chunk_stereo)), (0, 0)))
            chunk_mono = np.pad(chunk_mono, (0, frames - len(chunk_mono)))
            self.position = 0
        else:
            self.position += frames

        outdata[:] = chunk_stereo

        if self.visualizer:
            self.visualizer.process_audio(chunk_mono)

    def play(self):
        self.stream = sd.OutputStream(
            callback=self.audio_callback,
            channels=2,
            samplerate=SAMPLE_RATE,
            blocksize=CHUNK_SIZE
        )
        self.stream.start()
        print("Playback started.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MediaPlayer("test_audios/Kansas-City.mp3")
    player.load_audio()
    player.visualizer = AudioVisualizer(num_bars=20, smoothing=0.7)
    player.play()
    sys.exit(app.exec())