# %%
import vlc
import os
import time
import pandas as pd
import numpy as np
import requests
import multiprocessing
import matplotlib.pyplot as plt
import seaborn as sns

from IPython.display import clear_output

DATASET_PATH = r'./data/custom_qos_evaluation_all_combinations.csv'
STREAM_URL = 'http://131.234.250.116:9000/data/stream_1.m3u8'
MANO_URL = "thesismano1.cs.upb.de"

# -

class ExperimentClient():
    def __init__(self, url=STREAM_URL):
        stream_url = url
        instance = vlc.Instance("--vout=dummy --aout=dummy".split())
        
        self.media = instance.media_new(stream_url)
        self.player = instance.media_player_new()

        self.player.set_media(self.media)

        self.bitrates = []
        self.playing_time = 0

    def restart_player(self):
        self.player.stop()
        self.player.play()

    def start_player(self):
        self.player.play()

    def stop_player(self):
        self.player.stop()

    def consume_stream_proc(self, timeblock, return_dict):
        _counter = 0
        _just_starting = True
        self.start_player()
        # init_time = time.time()
        previous_bitrate = 0.0
        _same_bitrate_count = 0
        SAME_BITRATE_THRESHOLD = 2
        time.sleep(1)
        while(_counter < timeblock+1):
            try:
                stats = vlc.MediaStats() 
                state = str(self.media.get_state())
                _bitrate = 0.0
                if state in ["State.Opening", "State.Buffering", "State.Playing"]:
                    self.media.get_stats(stats)
                    _bitrate = stats.demux_bitrate*8000.0
                    # print("Bitrate")
                    # print(_bitrate)
                    # print(state)
                    if _bitrate == 0.0:
                        if _just_starting:
                            print("Streaming just started...")
                            _just_starting = False
                        else:
                            print("No data yet...")
                            return_dict["buffer_time"] +=1
                            # return_dict['down_time'] += 1
                    else:
                        if _bitrate == previous_bitrate:
                            if _same_bitrate_count >= SAME_BITRATE_THRESHOLD:
                                _same_bitrate_count = 0
                                print("Bitrate seems to be same, stream stuck? - Retrying...")
                                return_dict['down_time'] += SAME_BITRATE_THRESHOLD + 1
                                return_dict['playing_time'] -= SAME_BITRATE_THRESHOLD
                                self.restart_player()
                            else:
                                print("Same bitrate!")
                                _same_bitrate_count += 1
                                return_dict['bitrates'].append(_bitrate)
                                return_dict['playing_time'] += 1
                        else:
                            _same_bitrate_count = 0
                            return_dict['bitrates'].append(_bitrate)
                            return_dict['playing_time'] += 1

                else:
                    if _just_starting:
                        print("Streaming just started...")
                        _just_starting = False                    
                    else:
                        print("Streaming not 'Playing' - Retrying...")
                        return_dict['down_time'] += 1                    
                        self.restart_player()

            except Exception as e:
                print(e)

            print(state, return_dict["bitrates"][-3:], "P:", return_dict["playing_time"], 
                                      "D:", return_dict["down_time"], "B:", return_dict["buffer_time"])
            previous_bitrate = _bitrate
            time.sleep(1)
            _counter += 1

        self.stop_player()        
        return return_dict

def set_remote_version(version, host=MANO_URL, port=8898) :
    if "virtual_deployment_units_vm" in version:
        switch_type="VM"
    if "virtual_deployment_units_gpu" in version:
        switch_type="GPU"
    if "virtual_deployment_units_con" in version:
        switch_type="CON"

    _base_path = 'http://{0}:{1}/switch_version?version={2}'.format(host, port, switch_type)

    try:
        r = requests.get(_base_path, verify=False)
        # print("Switch Version")
        print("Switch Version: ", r.text)
    except Exception as e:
        print(e)
        print("Switch version could'nt be set")


# %%
# ## Read Policy Trace
TIMEBLOCK_MINUTES = 0.5

TIMEBLOCK = TIMEBLOCK_MINUTES * 60 # Sec

EXPERIMENT_START_TIME = int(time.time())

version_trace = pd.read_csv(DATASET_PATH, index_col=0)

print(version_trace.shape)

print("\nVersion Counts")
print(version_trace['version'].value_counts())

# # Run Experiments

# %%
# TIMEBLOCK = 60

# Setting initial version and waiting
set_remote_version(version_trace['version'][0])
time.sleep(30)

for index_label, row_series in version_trace.iterrows():

    print("Running Experiment at: ", index_label, " For: ", row_series['version'])

    # Switch version on MANO
    set_remote_version(row_series['version'])

    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    return_dict["bitrates"] = manager.list()
    return_dict["playing_time"] = 0
    return_dict["down_time"] = 0
    return_dict["buffer_time"] = 0

    _runner = ExperimentClient()

    p = multiprocessing.Process(target=_runner.consume_stream_proc, args=(TIMEBLOCK, return_dict))
    p.start()

    p.join()

    print("\n####################")
    print(np.mean(return_dict["bitrates"]), return_dict["playing_time"], return_dict["down_time"])
    print("####################\n")

    p.terminate()

    ################
    # Store Results 
    ################
    version_trace.at[index_label , 'avg_datarate'] = np.mean(return_dict["bitrates"])
    version_trace.at[index_label , 'playing_time'] = return_dict["playing_time"]
    version_trace.at[index_label , 'down_time'] = return_dict["down_time"]
    version_trace.at[index_label , 'buffer_time'] = return_dict["buffer_time"]

    clear_output(wait=True)

version_trace = version_trace.drop('index', axis=1)
# -

version_trace['total_downtime'] = version_trace['down_time'] + version_trace['buffer_time']
version_trace.to_csv('./data/results/custom_{}_combinations_qos_results.csv'.format(EXPERIMENT_START_TIME))
version_trace.head()

# %%
fig, ax1 = plt.subplots(figsize=(10,5))
plt.xticks(rotation=90)

x = version_trace.index
y1 = version_trace['avg_datarate']
y2 = version_trace['down_time']

ax2 = ax1.twinx()

ind = np.arange(len(x))
width = 0.35
# sns.set(style='whitegrid', palette='muted', font_scale=1.5)

# Bar
# rects1 = ax1.bar(ind - width/2, y1, width, label='Datarate',color = 'b')
# rects2 = ax2.bar(ind + width/2, y2, width, label='Downtime', color = 'g')

# Plot
ax1.plot(x, y1, 'g-', label='Datarate',color = 'b')
ax2.plot(x, y2, 'b-', label='Downtime', color = 'g')

ax1.set_xticks(ind)
ax1.set_xticklabels(version_trace['version'])

print(version_trace['avg_datarate'].mean())
print(version_trace['down_time'].sum())


fig.legend()
# fig = ax2.get_figure()
plt.show()
# -
