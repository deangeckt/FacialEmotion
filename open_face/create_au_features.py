import pandas as pd
import os
from collections import defaultdict
import numpy as np

raw_data_path = 'raw_data/'
au_list = ['AU01_r', 'AU02_r', 'AU04_r', 'AU05_r', 'AU06_r', 'AU07_r', 'AU09_r', 'AU10_r',
           'AU12_r', 'AU15_r', 'AU17_r', 'AU01_c', 'AU02_c', 'AU04_c', 'AU05_c', 'AU06_c', 'AU07_c',
           'AU09_c', 'AU10_c', 'AU12_c', 'AU14_c', 'AU15_c', 'AU17_c', 'AU28_c']
non_bin_aus = ['AU01_r', 'AU02_r', 'AU04_r', 'AU05_r', 'AU06_r', 'AU07_r', 'AU09_r', 'AU10_r',
               'AU12_r', 'AU15_r', 'AU17_r']
bin_aus = ['AU01_c', 'AU02_c', 'AU04_c', 'AU05_c', 'AU06_c', 'AU07_c', 'AU09_c', 'AU10_c',
           'AU12_c', 'AU15_c', 'AU17_c']
num_of_segments = 3


def default_au_features():
    au_features = {}
    for f in features:
        au_features[f] = []
    return au_features


def bin_sequence(bin_au):
    start = []
    stop = []

    for idx, v in enumerate(bin_au):
        if v == 1:
            if len(start) == len(stop):
                start.append(idx)
            elif idx == len(bin_au) - 1:
                stop.append(idx)
        if v == 0:
            if len(start) > len(stop):
                end = idx if idx == len(bin_au) - 1 else idx - 1
                stop.append(end)
    return start, stop


def extract_file(file_path):
    df = pd.read_csv(file_path)
    df = df.rename(columns=lambda x: x.strip())
    df = df[au_list]

    file_res = defaultdict(dict)

    for bin_au, au in zip(bin_aus, non_bin_aus):
        au_name = au.split('_')[0]
        file_res[au_name]['mean'] = df[au].mean()
        file_res[au_name]['std'] = df[au].std()

        au_segments = np.array_split(np.array(df[au]), num_of_segments)
        au_bin_segments = np.array_split(np.array(df[bin_au]), num_of_segments)

        for idx, au_bin_signal in enumerate(au_bin_segments):
            au_signal = au_segments[idx]
            seq_start, seq_end = bin_sequence(au_bin_signal)

            # Features
            events_count_ = len(seq_start)
            events_len_ = []
            events_intensity_ = []

            for st, end in zip(seq_start, seq_end):
                events_len_.append(end - st)
                events_intensity_.append(np.mean(au_signal[st:end]))

            event_key = f"e{idx}"
            file_res[au_name][f"{event_key}_length"] = np.mean(np.array(events_len_)) if events_count_ else 0
            file_res[au_name][f"{event_key}_intensity"] = np.mean(np.array(events_intensity_)) if events_count_ else 0
            file_res[au_name][f"{event_key}_amount"] = events_count_

    return file_res


features = ['mean', 'std',
            'e0_length', 'e1_length', 'e2_length'
            'e0_intensity', 'e1_intensity', 'e2_intensity',
            'e0_amount', 'e1_amount', 'e2_amount']
df_features = ['label', 'au'].extend(features)

all_vid_res = defaultdict(lambda: defaultdict(lambda: default_au_features()))
per_vid_res = defaultdict(dict)
os.makedirs("results", exist_ok=True)

for file_name in os.listdir(raw_data_path):
    print(file_name)
    label = file_name.split('_')[1]
    file_res = extract_file(os.path.join(raw_data_path, file_name))

    per_vid_res_df = pd.DataFrame(columns=df_features)
    for au in file_res:
        res_obj = {'label': label, 'au': au}
        for feature in features:
            val = file_res[au].get(feature, 0)
            all_vid_res[label][au][feature].append(val)
            res_obj[feature] = val
        per_vid_res_df = per_vid_res_df.append(res_obj, ignore_index=True)

    # save result per video / file
    per_vid_res_df.to_csv(f'results/{file_name}')


all_vid_res_df = pd.DataFrame(columns=df_features)
for label in all_vid_res:
    for au in all_vid_res[label]:
        res_obj = {'label': label, 'au': au}
        for feature in features:
            feature_mean = np.mean(np.array(all_vid_res[label][au][feature]))
            res_obj[feature] = feature_mean
        all_vid_res_df = all_vid_res_df.append(res_obj, ignore_index=True)

all_vid_res_df.to_csv('results/all_results.csv')
