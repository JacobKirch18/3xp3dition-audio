#!/usr/bin/env python3

import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel)
from PyQt6.QtCore import Qt, QTimer
from visualizer import AudioVisualizer
import soundfile as sf
import sounddevice as sd

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024

class MediaPlayerUI(QMainWindow):
    def __init__(self, audio_file):
        super().__init__()
        self.audio_file = audio_file
        self.stream = None
        self.audio_data_stereo = None
        self.audio_data_mono = None
        self.position = 0
        self.is_playing = False
        self.total_frames = 0

        self.init_ui()
        self.load_audio()

    def init_ui(self):
        self.setWindowTitle("Media Player")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.visualizer = AudioVisualizer(num_bars=20, smoothing=0.7)
        main_layout.addWidget(self.visualizer.win)

        self.progress_bar = QSlider(Qt.Orientation.Horizontal)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1000)
        self.progress_bar.sliderMoved.connect(self.seek)
        main_layout.addWidget(self.progress_bar)

        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        main_layout.addLayout(time_layout)

        controls_layout = QHBoxLayout()

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play_pause)
        controls_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop)
        controls_layout.addWidget(self.stop_button)

        controls_layout.addStretch()

        volume_label = QLabel("Volume:")
        controls_layout.addWidget(volume_label)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(150)
        controls_layout.addWidget(self.volume_slider)

        main_layout.addLayout(controls_layout)

        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_progress)
        self.ui_timer.start(100)

    def load_audio(self):
        data, sr = sf.read(self.audio_file, always_2d=True)

        if data.shape[1] > 1:
            self.audio_data_stereo = data
            self.audio_data_mono = np.mean(data, axis=1)
        else:
            self.audio_data_stereo = np.column_stack([data, data])
            self.audio_data_mono = data.flatten()

        self.total_frames = len(self.audio_data_mono)
        total_seconds = self.total_frames / SAMPLE_RATE
        self.total_time_label.setText(self.format_time(total_seconds))

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

        volume = self.volume_slider.value() / 100.0
        chunk_stereo *= volume

        outdata[:] = chunk_stereo
        self.visualizer.process_audio(chunk_mono)
    
    def toggle_play_pause(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def play(self):
        if not self.stream:
            self.stream = sd.OutputStream(
                callback=self.audio_callback,
                channels=2,
                samplerate=SAMPLE_RATE,
                blocksize=CHUNK_SIZE
            )
        self.stream.start()
        self.is_playing = True
        self.play_button.setText("Pause")
    
    def pause(self):
        if self.stream:
            self.stream.stop()
        self.is_playing = False
        self.play_button.setText("Play")
    
    def stop(self):
        if self.stream:
            self.stream.stop()
        self.position = 0
        self.is_playing = False
        self.play_button.setText("Play")
        self.visualizer.bar_heights = np.zeros(self.visualizer.num_bars)

    def seek(self, value):
        self.position = int((value / 1000) * self.total_frames)

    def update_progress(self):
        if self.total_frames > 0:
            progress = int((self.position / self.total_frames) * 1000)
            self.progress_bar.setValue(progress)

            current_seconds = self.position / SAMPLE_RATE
            self.current_time_label.setText(self.format_time(current_seconds))

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MediaPlayerUI("test_audios/Kansas-City.mp3")
    player.show()
    sys.exit(app.exec())