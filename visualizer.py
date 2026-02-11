import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

class AudioVisualizer:
    def __init__(self, num_bars=20, smoothing=0.7, sample_rate=44100):
        self.num_bars = num_bars
        self.smoothing = smoothing
        self.sample_rate = sample_rate
        self.bar_heights = np.zeros(num_bars)

        self.win = pg.plot(title="Audio Visualizer")
        self.win.setYRange(0, 500)
        self.win.setXRange(0, num_bars)
        self.win.setBackground('k')
        self.win.hideAxis('left')
        self.win.hideAxis('bottom')
        self.win.showGrid(x=False, y=False)

        colors = self._create_colors()

        self.bar_graph = pg.BarGraphItem(
            x=range(num_bars),
            height=self.bar_heights,
            width=0.8,
            brushes=colors
        )
        self.win.addItem(self.bar_graph)

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_display)
        self.timer.start(50)

    def _create_colors(self):
        colors = []
        for i in range(self.num_bars):
            ratio = i / self.num_bars
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
        return colors

    def process_audio(self, audio_data):
        fft_data = np.fft.rfft(audio_data)
        fft_magnitude = np.abs(fft_data)

        freq_bins = len(fft_magnitude)
        log_indices = np.logspace(np.log10(2), np.log10(freq_bins), self.num_bars, dtype=int)
        log_indices = np.concatenate(([0], log_indices))

        for i in range(1, len(log_indices)):
            if log_indices[i] <= log_indices[i-1]:
                log_indices[i] = log_indices[i-1] + 1

        new_heights = []
        for i in range(self.num_bars):
            start = log_indices[i]
            end = log_indices[i + 1]
            if start < end and end <= freq_bins:
                avg = np.mean(fft_magnitude[start:end])
                boost = 0.3 + (i / self.num_bars) * 10
                new_heights.append(avg * boost)
            else:
                new_heights.append(0)
        
        self.bar_heights = np.array(new_heights)

    def _update_display(self):
        current_heights = self.bar_graph.opts['height']
        target_heights = self.bar_heights * 3
        smoothed_heights = current_heights * self.smoothing + target_heights * (1 - self.smoothing)
        smoothed_heights = np.clip(smoothed_heights, 0, 480)
        self.bar_graph.setOpts(height=smoothed_heights)