import pandas as pd
import os
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

au_list = ['AU01_r', 'AU02_r', 'AU04_r', 'AU05_r', 'AU06_r', 'AU07_r', 'AU09_r', 'AU10_r',
           'AU12_r', 'AU15_r', 'AU17_r', 'AU01_c', 'AU02_c', 'AU04_c', 'AU05_c', 'AU06_c', 'AU07_c',
           'AU09_c', 'AU10_c', 'AU12_c', 'AU14_c', 'AU15_c', 'AU17_c', 'AU28_c']

non_bin_aus = [au for au in au_list if au.endswith('r')]
bin_aus = [au for au in au_list if au.endswith('c')]
num_of_segments = 3


class AuEvents:
    def __init__(self, au_id, label, person):
        self.label = label
        self.person = person
        self.au_id = au_id

        self.is_bin_au = au_id in bin_aus
        self.events = {}
        for i in range(num_of_segments):
            self.events[i] = []

        # Thresholds
        self.au_th_fix = 2  # fixing the dynamic threshold
        self.min_wd = 4  # min num of frames above dy threshold

        # calculating during process
        self.dy_au_th = None
        self.au = None
        self.segments = None

        self.start_idx = -1
        self.end_idx = -1

    def __add_event(self, segment_idx):
        self.events[segment_idx].append({'s': self.start_idx, 'e': self.end_idx})
        self.start_idx = -1
        self.end_idx = -1

    def __segment_event(self, segment, segment_idx):
        segments_len = [len(s) for s in self.segments]
        idx_offset = sum(segments_len[0:segment_idx])

        for idx, v in enumerate(segment):
            frame_idx = idx + idx_offset
            if v >= self.dy_au_th:
                if self.start_idx == -1:
                    self.start_idx = frame_idx
            else:
                if self.start_idx != -1:
                    curr_len = frame_idx - self.start_idx
                    if curr_len > self.min_wd:
                        self.end_idx = frame_idx
                        self.__add_event(segment_idx)

    def plot_events(self):
        if self.is_bin_au:
            return
        all_events = [item for sublist in self.events.values() for item in sublist]
        st_idx = [m['s'] for m in all_events]
        en_idx = [m['e'] for m in all_events]
        zeros = [0] * len(st_idx)
        plt.scatter(x=st_idx, y=zeros, color='green')
        plt.scatter(x=en_idx, y=zeros, color='red')

        plt.axhline(y=self.dy_au_th, color='purple', linestyle='-')
        for st in st_idx:
            plt.axvline(x=st, color='green', ls='--')
        for en in en_idx:
            plt.axvline(x=en, color='red', ls='--')

        plt.plot(self.au, label=self.au_id)
        plt.legend()
        plt.title(f"{self.person}-{self.label}: {self.au_id}")
        plt.show()

    def process(self, au: np.ndarray):
        self.au = au
        if self.is_bin_au:
            return 0, 0, 0

        self.dy_au_th = np.mean(self.au) * self.au_th_fix
        self.segments = np.array_split(au, num_of_segments)

        for idx, segment in enumerate(self.segments):
            self.__segment_event(segment, idx)

        return tuple([len(e) for e in self.events.values()])
