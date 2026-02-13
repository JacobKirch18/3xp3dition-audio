#!/usr/bin/env python3

import os
import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QListWidget)
from PyQt6.QtCore import Qt, QTimer
from visualizer import AudioVisualizer
import soundfile as sf
import sounddevice as sd
import threading

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024

class MediaPlayerUI(QMainWindow):
    def __init__(self, source_path=None, is_cd=False):
        super().__init__()
        self.source_path = source_path
        self.is_cd = is_cd
        self.cd_source = None
        self.playlist = []
        self.current_track_index = 0
        self.stream = None
        self.audio_data_stereo = None
        self.audio_data_mono = None
        self.position = 0
        self.is_playing = False
        self.total_frames = 0
        self.rip_queue = []
        self.ripping_thread = None

        self.init_ui()

        if is_cd:
            self.load_cd()
        else:
            self.load_playlist()

        self.load_audio()

    def init_ui(self):
        self.setWindowTitle("Media Player")
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_horizontal = QHBoxLayout(central_widget)

        self.track_list = QListWidget()
        self.track_list.setMaximumWidth(300)
        self.track_list.itemDoubleClicked.connect(self.track_selected)
        main_horizontal.addWidget(self.track_list)

        player_widget = QWidget()
        main_layout = QVBoxLayout(player_widget)
        main_horizontal.addWidget(player_widget)

        self.visualizer = AudioVisualizer(num_bars=20, smoothing=0.7)
        main_layout.addWidget(self.visualizer.win)

        self.song_label = QLabel("No song loaded")
        self.song_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.song_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        main_layout.addWidget(self.song_label)

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

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.previous_track)
        controls_layout.addWidget(self.prev_button)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play_pause)
        controls_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop)
        controls_layout.addWidget(self.stop_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_track)
        controls_layout.addWidget(self.next_button)

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

    def load_cd(self):
        from cd_audio_source import CDAudioSource

        self.cd_source = CDAudioSource()

        if not self.cd_source.detect_cd():
            print("No CD detected")
            return
        
        tracks = self.cd_source.get_track_info()

        for track in tracks:
            track_name = f"{track['number']:02d}. {track['title']}"
            self.playlist.append(track)
            self.track_list.addItem(track_name)

        self.setWindowTitle(f"CD Player - {self.cd_source.get_disc_info_string()}")

        print(f"Loaded {len(self.playlist)} tracks from CD")

    def start_background_ripper(self):
        self.rip_queue = list(range(2, len(self.playlist) + 1))

        def ripper_worker():
            while self.rip_queue:
                track_num = self.rip_queue.pop(0)
                print(f"Ripping track {track_num} in background...")
                self.cd_source.rip_track_to_wav(track_num)
        
        self.ripping_thread = threading.Thread(target=ripper_worker, daemon=True)
        self.ripping_thread.start()
        print("Background ripper started")

    def load_playlist(self):
        for filename in sorted(os.listdir(self.source_path)):
            if filename.lower().endswith('.mp3'):
                full_path = os.path.join(self.source_path, filename)
                self.playlist.append(full_path)
                self.track_list.addItem(filename)

    def load_audio(self):
        if not self.playlist:
            print("No audio files found in the folder.")
            return

        if self.is_cd:
            track_num = self.current_track_index + 1
            print(f"Ripping track {track_num} (foreground)...")
            wav_path = self.cd_source.rip_track_to_wav(track_num)

            if not wav_path:
                print(f"Failed to rip track {track_num}.")
                return
            
            current_file = wav_path
            track_info = self.playlist[self.current_track_index]
            self.song_label.setText(f"{track_num:02d}. {track_info['title']}")

            if not self.ripping_thread or not self.ripping_thread.is_alive():
                self.start_background_ripper()

        else:
            current_file = self.playlist[self.current_track_index]
            self.song_label.setText(os.path.basename(current_file))
        
        data, sr = sf.read(current_file, always_2d=True)
        self.track_list.setCurrentRow(self.current_track_index)

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
    
    def previous_track(self):
        was_playing = self.is_playing
        self.stop()

        self.current_track_index -= 1
        if self.current_track_index < 0:
            self.current_track_index = len(self.playlist) - 1

        self.load_audio()
        if was_playing:
            self.play()

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

    def next_track(self):
        was_playing = self.is_playing
        self.stop()

        self.current_track_index += 1
        if self.current_track_index >= len(self.playlist):
            self.current_track_index = 0

        self.load_audio()
        if was_playing:
            self.play()

    def track_selected(self, item):
        was_playing = self.is_playing
        self.stop()

        self.current_track_index = self.track_list.currentRow()

        self.load_audio()
        if was_playing:
            self.play()

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

    def closeEvent(self, event):
        print("Closing application, cleaning up...")
        
        if hasattr(self, 'ui_timer'):
            self.ui_timer.stop()
        
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                print(f"Error stopping stream: {e}")
        
        self.audio_data_stereo = None
        self.audio_data_mono = None
        
        import time
        time.sleep(0.1)
        
        if self.is_cd and self.cd_source:
            print(f"Attempting to clean up {len(self.cd_source.ripped_files)} files...")
            self.cd_source.cleanup_temp_files()
        
        event.accept()
    
if __name__ == "__main__":
    app = QApplication(sys.argv)

    if len(sys.argv) > 1 and sys.argv[1] == "--cd":
        player = MediaPlayerUI(is_cd=True)
    else:
        player = MediaPlayerUI("test_audios")

    player.show()
    sys.exit(app.exec())