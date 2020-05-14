# -*- coding: utf-8 -*-
# %%
# ## 1. Get PD
# -
import os
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
from sklearn import preprocessing
import numpy as np
import pandas as pd
import time
import requests
import yaml
import random
from glob import glob

from skcriteria import Data, MIN, MAX
from skcriteria.madm import closeness, simple

# %%
START_TIME = time.time()
LIMIT_DATASET = False

LOOK_AHEAD = 5  # Mins (factor of shape)
EXPERIMENT_RUNS = 1

DATASET_PATH = r'/plugins/son-mano-traffic-forecast/notebooks/data/varience_manual/'
DEBUG_FILE = r'./data/varience_manual/results/output_debug.log'
traffic_files = [y for x in os.walk(DATASET_PATH) for y in glob(os.path.join(x[0], '*.csv'))]
traffic_files.sort()

# DATASET_PATH = r'/plugins/son-mano-traffic-forecast/notebooks/data/dataset_six_traffic.csv'
_SCORE_MIN, _SCORE_MAX = 1, 5

# WEIGHTS --> [cost, over_provision, overhead, support_deviation, same_version]
WEIGHTS = {
    "negative": {
        "cost": 9,
        "over_provision": 9,
        "overhead": 1
    },
    "positive": {
        "support_deviation": 1,
        "same_version": 3,
        "support_max": 0,
        "support_recent_history": 0
    }
}

# accuracy_list = [1.0]
accuracy_list = [1.0]
# accuracy_list = [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6]

# %%
r = requests.get(
    'https://raw.githubusercontent.com/CN-UPB/Pishahang/mvp-thesis/pish-examples/pwm-scripts/descriptors/multiversion/transcoder_mv_policy.yml')
# print(r.text)
PD = yaml.load(r.text, Loader=yaml.FullLoader)


# PD["versions"] = {
#     'virtual_deployment_units_gpu': {'transcoder-image-1-gpu': {'cost_per_min': 0.0087,
#                                                                 'max_data_rate': 3000,
#                                                                 'management_overhead': 6}},
#     'virtual_deployment_units_con': {'transcoder-image-1-con': {'cost_per_min': 0.00045,
#                                                                 'max_data_rate': 1200,
#                                                                 'management_overhead': 6}}}

VM_COST_PER_MINUTE = PD["versions"]['virtual_deployment_units_vm']["transcoder-image-1-vm"]['cost_per_min']
CON_COST_PER_MINUTE = PD["versions"]['virtual_deployment_units_con']["transcoder-image-1-con"]['cost_per_min']
GPU_COST_PER_MINUTE = PD["versions"]['virtual_deployment_units_gpu']["transcoder-image-1-gpu"]['cost_per_min']

# for _vm_type_key, _vm_type_value in PD["versions"].items():
#     print(_vm_type_key)
#     for _vm_version_key, _vm_version_value in _vm_type_value.items():
#         print(_vm_version_key)
#         print(_vm_version_value)
#         print("\n")

# %% endofcell="--"

'''
Find the version with the max supported datarate
'''


def find_max_datarate_version(versions):
    _max_datarate = 0

    for _vm_type_key, _vm_type_value in versions.items():
        # print(_vm_type_key)

        for _vm_version_key, _vm_version_value in _vm_type_value.items():
            # print(_vm_version_key)
            # print(_vm_version_value["max_data_rate"])

            if _vm_version_value["max_data_rate"] > _max_datarate:
                _max_datarate = _vm_version_value["max_data_rate"]
                _max_datarate_version = {_vm_type_key: {
                    _vm_version_key: _vm_version_value}}

    return _max_datarate_version


'''
Get all the versions that can support the datarate demand
'''


def get_supported_versions(prediction, versions):
    # Iterate versions
    datarate_supported_versions = {}

    for _vm_type_key, _vm_type_value in versions.items():
        # print(_vm_type_key)

        for _vm_version_key, _vm_version_value in _vm_type_value.items():
            # print(_vm_version_key)
            # print(_vm_version_value["max_data_rate"])
            # print(prediction["mean"])
            if _vm_version_value["max_data_rate"] >= prediction["mean"]:
                # check if key present else add
                if _vm_type_key in datarate_supported_versions:
                    datarate_supported_versions[_vm_type_key][_vm_version_key] = _vm_version_value
                else:
                    datarate_supported_versions[_vm_type_key] = {}
                    datarate_supported_versions[_vm_type_key][_vm_version_key] = _vm_version_value

    if len(datarate_supported_versions) == 0:
        return find_max_datarate_version(versions)
    return datarate_supported_versions


'''
Interpolate data points to a certain range
'''


def interpolate_array(values, min=_SCORE_MIN, max=_SCORE_MAX):
    return np.interp(values, (values.min(), values.max()), (min, max))


'''
Build the decision matrix for a given traffic prediction values 
'''


def build_decision_matrix(prediction, meta, versions):
    _decision_matrix = {}
    for _vm_type_key, _vm_type_value in versions.items():
        for _vm_version_key, _vm_version_value in _vm_type_value.items():
            if _vm_type_key not in _decision_matrix:
                _decision_matrix[_vm_type_key] = {}
            if _vm_version_key not in _decision_matrix[_vm_type_key]:
                _decision_matrix[_vm_type_key][_vm_version_key] = {}

            # Cost
            _decision_matrix[_vm_type_key][_vm_version_key]["cost"] = _vm_version_value['cost_per_min']

            # Support deviation
            if _vm_version_value['max_data_rate'] > (prediction['mean'] + prediction['std']):
                _decision_matrix[_vm_type_key][_vm_version_key]["support_deviation"] = 5
            else:
                _decision_matrix[_vm_type_key][_vm_version_key]["support_deviation"] = 1

            # Over Provision
            _decision_matrix[_vm_type_key][_vm_version_key]["over_provision"] = int(
                _vm_version_value['max_data_rate']) - int(prediction['mean'])

            # Same Version
            if meta["current_version"] == _vm_version_key:
                _decision_matrix[_vm_type_key][_vm_version_key]["same_version"] = 5
            else:
                _decision_matrix[_vm_type_key][_vm_version_key]["same_version"] = 1

            # Overhead
            _decision_matrix[_vm_type_key][_vm_version_key]["overhead"] = _vm_version_value['management_overhead']

            # Support max datarate
            if _vm_version_value['max_data_rate'] >= (prediction['max']):
                _decision_matrix[_vm_type_key][_vm_version_key]["support_max"] = 5
            else:
                _decision_matrix[_vm_type_key][_vm_version_key]["support_max"] = 1

            # Support recent history
            if _vm_version_value['max_data_rate'] >= (meta["recent_history"]["mean"]):
                _decision_matrix[_vm_type_key][_vm_version_key]["support_recent_history"] = 5
            else:
                _decision_matrix[_vm_type_key][_vm_version_key]["support_recent_history"] = 1

    decision_matrix_df = pd.DataFrame.from_dict({(i, j): _decision_matrix[i][j]
                                                 for i in _decision_matrix.keys()
                                                 for j in _decision_matrix[i].keys()},
                                                orient='index')

    decision_matrix_df["over_provision"] = interpolate_array(
        decision_matrix_df["over_provision"])
    decision_matrix_df["cost"] = interpolate_array(decision_matrix_df["cost"])
    decision_matrix_df["overhead"] = interpolate_array(
        decision_matrix_df["overhead"])

    return decision_matrix_df


'''
Get policy decision given decision matrix and weights
'''


def get_policy_decision(decision_matrix, weights):

    # Negative
    cost = -1 * weights["negative"]["cost"]
    over_provision = -1 * weights["negative"]["over_provision"]
    overhead = -1 * weights["negative"]["overhead"]

    # Positive
    support_deviation = weights["positive"]['support_deviation']
    same_version = weights["positive"]['same_version']
    support_max = weights["positive"]['support_max']
    support_recent_history = weights["positive"]['support_recent_history']

    # WEIGHTS --> [cost, over_provision, overhead, support_deviation, same_version]
    weights_row = [cost, over_provision,
                   overhead, support_deviation, same_version, support_max, support_recent_history]

    for index_label, row_series in decision_matrix.iterrows():
        _row = np.array([row_series.cost, row_series.over_provision, row_series.overhead,
                         row_series.support_deviation, row_series.same_version, row_series.support_max, 
                         row_series.support_recent_history])

        decision_matrix.at[index_label, 'score'] = np.dot(
            np.array(weights_row), _row)

    _version = decision_matrix[decision_matrix.score ==
                               decision_matrix.score.max()].index[0]
    return _version

def get_policy_decision_mcda(decision_matrix, weights, mcda_method="WPM"):
    # Negative
    cost = weights["negative"]["cost"]
    over_provision = weights["negative"]["over_provision"]
    overhead = weights["negative"]["overhead"]
    support_deviation = weights["positive"]['support_deviation']
    same_version = weights["positive"]['same_version']
    support_max = weights["positive"]['support_max']
    support_recent_history = weights["positive"]['support_recent_history']

    c_cost = MIN
    c_over_provision = MIN
    c_overhead = MIN
    c_support_deviation = MAX
    c_same_version = MAX
    c_support_max = MAX
    c_support_recent_history = MAX

    _weights = [cost, support_deviation, over_provision,
                    same_version, overhead, support_max, support_recent_history]

    criteria = [c_cost, c_support_deviation, c_over_provision,
                    c_same_version, c_overhead, c_support_max, c_support_recent_history]

    data = Data(decision_matrix.values, criteria,
            weights=_weights,
            anames=decision_matrix.index,
            cnames=list(decision_matrix.columns))

    if mcda_method == "WPM":
        dm = simple.WeightedProduct()
    elif mcda_method == "WSM":
        dm = simple.WeightedSum()
    elif mcda_method == "TOPSIS":
        dm = closeness.TOPSIS()

    dec = dm.decide(data)

    # print(dec.e_.points)
    return data.anames[dec.best_alternative_]


'''
Find the version with least cost
'''
def find_cheapest_version(versions):
    _cost = None

    for _vm_type_key, _vm_type_value in versions.items():
        # print(_vm_type_key)

        for _vm_version_key, _vm_version_value in _vm_type_value.items():
            # print(_vm_version_key)
            # print(_vm_version_value["max_data_rate"])
            # FIXME: cost_per_min should be int
            if _cost is None:
                _cost = _vm_version_value["cost_per_min"]
                _cost_version = (_vm_type_key, _vm_version_key)

            if float(_vm_version_value["cost_per_min"]) < float(_cost):
                _cost = _vm_version_value["cost_per_min"]
                # _cost_version = { _vm_type_key: { _vm_version_key : _vm_version_value } }
                _cost_version = (_vm_type_key, _vm_version_key)

    return _cost_version

def get_switch_price(current_version, previous_version):
    _price = 0
    if "vm" in previous_version:
        if "vm" in current_version:
            _price = 0
        if "con" in current_version:
            _price = (5/60) * VM_COST_PER_MINUTE
        if "gpu" in current_version:
            _price = (5/60) * VM_COST_PER_MINUTE

    if "con" in previous_version:
        if "con" in current_version:
            _price = 0
        if "vm" in current_version:
            _price = (85/60) * CON_COST_PER_MINUTE
        if "gpu" in current_version:
            _price = (5/60) * CON_COST_PER_MINUTE

    if "gpu" in previous_version:
        if "gpu" in current_version:
            _price = 0
        if "vm" in current_version:
            _price = (85/60) * GPU_COST_PER_MINUTE
        if "con" in current_version:
            _price = (5/60) * GPU_COST_PER_MINUTE

    return _price

def get_switch_qos_metrics(current_version, previous_version):
    qos_metrics = {}
    if "vm" in previous_version:
        if "vm" in current_version:
            # qos_metrics['datarate'] = 668
            qos_metrics['downtime'] = 0
            qos_metrics['buffertime'] = 0
            qos_metrics['switchtime'] = 0
        if "con" in current_version:
            # qos_metrics['datarate'] = 668
            qos_metrics['downtime'] = 3
            qos_metrics['buffertime'] = 3
            qos_metrics['switchtime'] = 5
        if "gpu" in current_version:
            # qos_metrics['datarate'] = 5275
            qos_metrics['downtime'] = 3
            qos_metrics['buffertime'] = 3
            qos_metrics['switchtime'] = 5

    if "con" in previous_version:
        if "con" in current_version:
            # qos_metrics['datarate'] = 668
            qos_metrics['downtime'] = 0
            qos_metrics['buffertime'] = 0
            qos_metrics['switchtime'] = 0
        if "vm" in current_version:
            # qos_metrics['datarate'] = 668
            qos_metrics['downtime'] = 3
            qos_metrics['buffertime'] = 3
            qos_metrics['switchtime'] = 85
        if "gpu" in current_version:
            # qos_metrics['datarate'] = 5415
            qos_metrics['downtime'] = 3
            qos_metrics['buffertime'] = 3
            qos_metrics['switchtime'] = 5

    if "gpu" in previous_version:
        if "gpu" in current_version:
            # qos_metrics['datarate'] = 5800
            qos_metrics['downtime'] = 0
            qos_metrics['buffertime'] = 0
            qos_metrics['switchtime'] = 0
        if "vm" in current_version:
            # qos_metrics['datarate'] = 2020
            qos_metrics['downtime'] = 3
            qos_metrics['buffertime'] = 3
            qos_metrics['switchtime'] = 85
        if "con" in current_version:
            # qos_metrics['datarate'] = 825
            qos_metrics['downtime'] = 3
            qos_metrics['buffertime'] = 3
            qos_metrics['switchtime'] = 5

    return qos_metrics


def get_binomial_samples(size, n=1, p=0.9):
    return np.random.binomial(n, p, size)


def get_prob_new_datarate(datarate, p=0.5, accuracy=0.9):
    delta = (1.0 - accuracy) * datarate

    if random.random() < p:
        new_datarate = datarate + delta
    else:
        new_datarate = datarate - delta

    return new_datarate


# -

# # Run Policy on Dataset

# %%
##################################
# Functions for experiment runner
##################################


def get_decision_dataset(traffic_grouped, traffic_history):
    switch_counter = {"pc_{}".format(
        int(_acc*100)): 0 for _acc in accuracy_list}
    switch_counter['history'] = 0
    switch_counter['history_grouped'] = 0
    _results = {}

    # Run Policy on Dataset
    for _acc in accuracy_list:
        _acc_pc = "pc_{}".format(int(_acc*100))
        _results[_acc_pc] = traffic_grouped[_acc_pc].copy()
        if _acc_pc == "pc_100":
            _results['history_grouped'] = traffic_grouped[_acc_pc].copy()
        # traffic_policy_test.plot()

        # iterate over the dataframe row by row and set version
        meta = {
            "current_version": "transcoder-image-1-vm",
            "current_version_history_grouped": "transcoder-image-1-vm",
            "recent_history": None
        }

        with open(DEBUG_FILE, "a") as f:
            for index_label, row_series in _results[_acc_pc].iterrows():
                if meta["recent_history"] is None:
                    meta["recent_history"] = row_series

                supported_versions = get_supported_versions(
                    prediction=row_series, versions=PD["versions"])


                decision_matrix_df = build_decision_matrix(
                    prediction=row_series, meta=meta, versions=supported_versions)

                _selected_version = ":".join(
                    get_policy_decision_mcda(decision_matrix_df, WEIGHTS, mcda_method="WPM"))
                _results[_acc_pc].at[index_label, 'policy'] = _selected_version

                if not _selected_version.split(":")[1] == meta["current_version"]:
                    switch_counter[_acc_pc] += 1

                f.write("\nrecent_history\n")
                f.write(str(meta["recent_history"]))
                f.write("\nForecast\n")
                f.write(str(row_series))

                if _acc_pc == "pc_100":
                    supported_versions_history = get_supported_versions(
                        prediction=meta['recent_history'], versions=PD["versions"])

                    _selected_version_history_grouped = ":".join(find_cheapest_version(versions=supported_versions_history))
                    _results['history_grouped'].at[index_label , 'history_grouped'] = _selected_version_history_grouped

                    if not _selected_version_history_grouped.split(":")[1] == meta["current_version_history_grouped"]:
                        switch_counter["history_grouped"] += 1

                    meta = {
                        "current_version": _selected_version.split(":")[1],
                        "current_version_history_grouped": _selected_version_history_grouped.split(":")[1],
                        "recent_history": row_series,
                    } 

                else:

                    meta = {
                        "current_version": _selected_version.split(":")[1],
                        "recent_history": row_series
                    }

                f.write("\n\n_selected_version\n")
                f.write(_selected_version)
                f.write("\n\n")
                f.write(str(decision_matrix_df))
                f.write("\n\n")

    # Run for History
    meta = {
        "current_version_history": "transcoder-image-1-vm",
        "recent_history": None
    }

    row_counter = 0

    for index_label, row_series in traffic_history.iterrows():
        if meta["recent_history"] is None:
            meta["recent_history"] = row_series['sent']

        # print(row_series)

        supported_versions_history = get_supported_versions(
            prediction={"mean": meta['recent_history']}, versions=PD["versions"])

        _selected_version_history = ":".join(
            find_cheapest_version(versions=supported_versions_history))
        traffic_history.at[index_label, 'history'] = _selected_version_history

        if not _selected_version_history.split(":")[1] == meta["current_version_history"]:
            switch_counter["history"] += 1

        meta = {
            "current_version_history": _selected_version_history.split(":")[1],
            "recent_history": row_series['sent']
        }

        row_counter += 1

    # Merge Data
    final_decision_dataset = pd.DataFrame()
    for _acc in accuracy_list:
        _acc_pc = "pc_{}".format(int(_acc*100))

        final_decision_dataset[_acc_pc] = _results[_acc_pc].iloc[np.repeat(np.arange(
            len(_results[_acc_pc])), LOOK_AHEAD)].reset_index().drop('index', axis=1)['policy']

        print("\npc_{}".format(int(_acc*100)))
        print(final_decision_dataset[_acc_pc].value_counts())

    final_decision_dataset['history'] = traffic_history['history']

    print("\nHistory")
    print(final_decision_dataset['history'].value_counts())

    print("Switch Stats")
    print(switch_counter)
    print("\n\n")

    return {
        "switch_counter": switch_counter,
        "final_decision_dataset": final_decision_dataset
    }


def get_qos_dataset(final_decision_dataset):
    qos_final_decision_dataset = pd.DataFrame()

    qos_results = {}

    for _acc in accuracy_list:
        _acc_pc = "pc_{}".format(int(_acc*100))
        _previous_version = None
        _current_version = None

        qos_results[_acc_pc] = {
            # 'datarate': [],
            'downtime': [],
            'buffertime': [],
            'switchtime': [],
            'wrongversion': [],
            'under_utilized': [],
            'over_loaded': []
        }

        for index_label, row_series in final_decision_dataset.iterrows():
            if _previous_version == None:
                _previous_version = row_series[_acc_pc]

            _current_version = row_series[_acc_pc]
            _proper_version = row_series['pc_100']

            qos_metrics = get_switch_qos_metrics(
                _current_version, _previous_version)

            if _proper_version != _current_version:
                # print(_proper_version, _current_version, _acc_pc)
                qos_metrics['wrongversion'] = 1
                qos_metrics['under_utilized'] = 0
                qos_metrics['over_loaded'] = 0

                if "gpu" in _proper_version:
                    # VNF is overloaded
                    qos_metrics['over_loaded'] = 1
                if "vm" in _proper_version:
                    if "gpu" in _current_version:
                        qos_metrics['under_utilized'] = 1
                if "con" in _proper_version:
                    if "gpu" in _current_version:
                        qos_metrics['under_utilized'] = 1
            else:
                qos_metrics['wrongversion'] = 0
                qos_metrics['under_utilized'] = 0
                qos_metrics['over_loaded'] = 0

            for _k in qos_metrics.keys():
                qos_results[_acc_pc][_k].append(qos_metrics[_k])

            _previous_version = _current_version

    # For History
    _previous_version = None
    _current_version = None
    _acc_pc = "history"

    qos_results[_acc_pc] = {
        # 'datarate': [],
        'downtime': [],
        'buffertime': [],
        'switchtime': [],
        'wrongversion': [],
        'under_utilized': [],
        'over_loaded': []
    }

    for index_label, row_series in final_decision_dataset.iterrows():
        if _previous_version == None:
            _previous_version = row_series[_acc_pc]

        _current_version = row_series[_acc_pc]
        _proper_version = row_series['pc_100']

        qos_metrics = get_switch_qos_metrics(
            _current_version, _previous_version)

        if _proper_version != _current_version:
            # print(_proper_version, _current_version, _acc_pc)
            qos_metrics['wrongversion'] = 1
            qos_metrics['under_utilized'] = 0
            qos_metrics['over_loaded'] = 0

            if "gpu" in _proper_version:
                # VNF is overloaded
                qos_metrics['over_loaded'] = 1
            if "vm" in _proper_version:
                if "gpu" in _current_version:
                    qos_metrics['under_utilized'] = 1
            if "con" in _proper_version:
                if "gpu" in _current_version:
                    qos_metrics['under_utilized'] = 1
        else:
            qos_metrics['wrongversion'] = 0
            qos_metrics['under_utilized'] = 0
            qos_metrics['over_loaded'] = 0

        for _k in qos_metrics.keys():
            qos_results[_acc_pc][_k].append(qos_metrics[_k])

        _previous_version = _current_version
    qos_final_decision_dataset = pd.DataFrame.from_dict({(i, j): qos_results[i][j]
                                                         for i in qos_results.keys()
                                                         for j in qos_results[i].keys()})

    return {
        "qos_final_decision_dataset": qos_final_decision_dataset,
        "qos_final_decision_dataset_sum": qos_final_decision_dataset.sum()
    }


def get_total_price(final_decision_dataset):
    _type = []
    _prices = []

    _result = {}

    skip_history = False
    for _acc in accuracy_list:
        _acc_pc = "pc_{}".format(int(_acc*100))
        _acc_price = 0
        _value_counts = final_decision_dataset[_acc_pc].value_counts()

        _result[_acc_pc] = {
            # 'datarate': [],
            'total_cost': [],
            'deployment_cost': [],
            'switching_cost': []
        }

        for k, v in _value_counts.iteritems():
            if "gpu" in k:
                _acc_price += (GPU_COST_PER_MINUTE  * v)
            if "vm" in k:
                _acc_price += (VM_COST_PER_MINUTE * v)
            if "con" in k:
                _acc_price += (CON_COST_PER_MINUTE * v)

        # Calculate cost of switching
        _previous_version = None
        _current_version = None
        _switch_price = 0

        for index_label, row_series in final_decision_dataset.iterrows():
            if _previous_version == None:
                _previous_version = row_series[_acc_pc]

            _current_version = row_series[_acc_pc]

            _switch_price += get_switch_price(
                _current_version, _previous_version)

            _previous_version = _current_version

        _result[_acc_pc]['total_cost'].append(_acc_price + _switch_price)
        _result[_acc_pc]['deployment_cost'].append(_acc_price)
        _result[_acc_pc]['switching_cost'].append(_switch_price)


    # For history 
    _acc_pc = "history"
    _acc_price = 0

    _result[_acc_pc] = {
        'total_cost': [],
        'deployment_cost': [],
        'switching_cost': []
    }

    _value_counts = final_decision_dataset[_acc_pc].value_counts()

    for k, v in _value_counts.iteritems():
        # print(k, v)
        if "gpu" in k:
            _acc_price += (GPU_COST_PER_MINUTE * v)
        if "vm" in k:
            _acc_price += (VM_COST_PER_MINUTE * v)
        if "con" in k:
            _acc_price += (CON_COST_PER_MINUTE * v)

    # Calculate cost of switching
    _previous_version = None
    _current_version = None
    _switch_price = 0

    for index_label, row_series in final_decision_dataset.iterrows():
        if _previous_version == None:
            _previous_version = row_series[_acc_pc]

        _current_version = row_series[_acc_pc]

        _switch_price += get_switch_price(
            _current_version, _previous_version)

        _previous_version = _current_version

    _result[_acc_pc]['total_cost'].append(_acc_price + _switch_price)
    _result[_acc_pc]['deployment_cost'].append(_acc_price)
    _result[_acc_pc]['switching_cost'].append(_switch_price)

    ADD_NON_MV_COSTS = False
    if ADD_NON_MV_COSTS:
        _no_deployments = final_decision_dataset.shape[0]

        for k, v in _value_counts.iteritems():
            # print(k, v)
            if "gpu" in k:       
                _acc_price = _no_deployments * GPU_COST_PER_MINUTE
                _switch_price = 0

                _result["gpu_only"] = {
                        'total_cost': [(_acc_price + _switch_price)],
                        'deployment_cost': [_acc_price],
                        'switching_cost': [0]
                    }
            if "vm" in k:
                _acc_price = _no_deployments * VM_COST_PER_MINUTE
                _switch_price = 0

                _result["vm_only"] = {
                        'total_cost': [(_acc_price + _switch_price)],
                        'deployment_cost': [_acc_price],
                        'switching_cost': [0]
                    }
            if "con" in k:
                _acc_price = _no_deployments * CON_COST_PER_MINUTE
                _switch_price = 0

                _result["con_only"] = {
                        'total_cost': [(_acc_price + _switch_price)],
                        'deployment_cost': [_acc_price],
                        'switching_cost': [0]
                    }

    price_final_decision_dataset = pd.DataFrame.from_dict({(i, j): _result[i][j]
                                                         for i in _result.keys()
                                                         for j in _result[i].keys()})    
    return(price_final_decision_dataset.sum())
# ## Random errors to get different accuracies
# %%

# http://patorjk.com/software/taag/#p=display&f=ANSI%20Regular&t=Run%20EXP

#####################################################
#####################################################
#
# ██████  ██    ██ ███    ██     ███████ ██   ██ ██████
# ██   ██ ██    ██ ████   ██     ██       ██ ██  ██   ██ 
# ██████  ██    ██ ██ ██  ██     █████     ███   ██████  
# ██   ██ ██    ██ ██  ██ ██     ██       ██ ██  ██
# ██   ██  ██████  ██   ████     ███████ ██   ██ ██
#
#####################################################
#####################################################

try:
    os.remove(DEBUG_FILE)
except:
    print("Error while deleting file ", DEBUG_FILE)

_traffic_results = {}

for _traffic_file in traffic_files:
    _traffic_file_name = os.path.basename(_traffic_file)

    with open(DEBUG_FILE, "a") as f:
        f.write("\n\nTRAFFIC FILE\n")
        f.write(_traffic_file_name)
        
    traffic_training_complete = pd.read_csv(_traffic_file, index_col=0)

    if LIMIT_DATASET:
        traffic_training_complete = traffic_training_complete[:LIMIT_DATASET]

    print(_traffic_file_name)
    print(traffic_training_complete.shape)
    traffic_training_complete.head(5)

    # Generate different probabalistic datasets
    for _acc in accuracy_list:
        _acc_pc = "pc_{}".format(int(_acc*100))

        _acc_samples = get_binomial_samples(
            size=traffic_training_complete.shape[0], n=1, p=_acc)

        traffic_training_complete[_acc_pc] = np.where(_acc_samples,
                                                    traffic_training_complete['sent'],
                                                    get_prob_new_datarate(traffic_training_complete['sent'], accuracy=_acc))

    # Group data according to look ahead
    traffic_grouped = traffic_training_complete.groupby(
        np.arange(len(traffic_training_complete))//LOOK_AHEAD).agg(['mean', 'std', 'min', 'max'])

    traffic_history = traffic_training_complete.reset_index().copy().drop('index', axis=1)

# Get decision dataset
    decision_results = get_decision_dataset(traffic_grouped, traffic_history)

    _traffic_results[_traffic_file_name] = decision_results


# %%

#####################################################
#####################################################
#
# ██████  ███████ ███████ ██    ██ ██   ████████ ███████ 
# ██   ██ ██      ██      ██    ██ ██      ██    ██      
# ██████  █████   ███████ ██    ██ ██      ██    ███████ 
# ██   ██ ██           ██ ██    ██ ██      ██         ██ 
# ██   ██ ███████ ███████  ██████  ███████ ██    ███████ 
#
#####################################################
#####################################################

# https://stackoverflow.com/questions/53766397/how-to-center-the-grid-of-a-plot-on-scatter-points
# https://stackoverflow.com/questions/47684652/how-to-customize-marker-colors-and-shapes-in-scatter-plot
markers = ["v" , "^" , "v" , ">" , "^" , "<", ">"]
colors = ['r','g','b','c','m', 'y', 'k']

fig, ax = plt.subplots(5, figsize=(8,8))
_counter = 0
for _traffic_file in traffic_files:

    _traffic_file_name = os.path.basename(_traffic_file)

    traffic_training_complete = pd.read_csv(_traffic_file, index_col=0)

    if LIMIT_DATASET:
        traffic_training_complete = traffic_training_complete[:LIMIT_DATASET]

    _res = _traffic_results[_traffic_file_name]

    x = _res["final_decision_dataset"].index
    y = [_res["final_decision_dataset"].history, _res["final_decision_dataset"].pc_100]
    labels = ['history', 'pc_100']

    # traffic_policy_test.reset_index().plot.scatter(figsize=(20,10), fontsize=20, x=x, y=y, marker="v")

    # ax[_counter+1].plot(traffic_training_complete["sent"],drawstyle='steps-pre')

    for i in range(len(labels)): #for each of the 7 features 
        mi = markers[i] #marker for ith feature 
        xi = x #x array for ith feature .. here is where you would generalize      different x for every feature
        yi = y[i] #y array for ith feature 
        ci = colors[i] #color for ith feature 
        ax[_counter].scatter(xi,yi, marker=mi, color=ci, s=49, label=labels[i])

        # ax[_counter].set_title(_traffic_file_name)
        ax[_counter].set_title("{} | Policy:{} | History:{}".format(_traffic_file_name, _res["switch_counter"]["pc_100"], _res["switch_counter"]["history"]))


        ax[_counter].set_yticks(np.arange(3))
        ax[_counter].set_yticks(np.arange(3+1)-0.5, minor=True)

        ax[_counter].set_xticks(np.arange(len(y[0])))
        ax[_counter].set_xticks(np.arange(len(y[0])+1)-0.5, minor=True)

        loc = plticker.MultipleLocator(base=5.0) # this locator puts ticks at regular intervals
        ax[_counter].xaxis.set_major_locator(loc)
        ax[_counter].grid(True, which="minor")
        ax[_counter].set_aspect("equal")


    _counter += 1

plt.legend(loc="upper left", bbox_to_anchor=(1.05, 1))
plt.show()

fig.savefig("./results/manual_variation_decision_scatter.png",
            format='png',
            dpi=300)

# %%
fig, ax = plt.subplots(5, figsize=(8,8))
_counter = 0
for _traffic_file in traffic_files:

    _traffic_file_name = os.path.basename(_traffic_file)

    traffic_training_complete = pd.read_csv(_traffic_file, index_col=0)

    if LIMIT_DATASET:
        traffic_training_complete = traffic_training_complete[:LIMIT_DATASET]

    _res = _traffic_results[_traffic_file_name]

    x = _res["final_decision_dataset"].index
    y = [_res["final_decision_dataset"].history, _res["final_decision_dataset"].pc_100]
    labels = ['history', 'pc_100']

    # traffic_policy_test.reset_index().plot.scatter(figsize=(20,10), fontsize=20, x=x, y=y, marker="v")
    ax[_counter].plot(traffic_training_complete["sent"],drawstyle='steps-pre')

        # ax[_counter].set_title(_traffic_file_name)
    ax[_counter].set_title("{} | Policy:{} | History:{}".format(_traffic_file_name, _res["switch_counter"]["pc_100"], _res["switch_counter"]["history"]))

    _counter += 1

plt.legend(loc="upper left", bbox_to_anchor=(1.05, 1))
plt.show()

fig.savefig("./results/manual_variation_decision_plot.png",
            format='png',
            dpi=300)



# %%

_acc_pc = "pc_100"
_results = traffic_grouped[_acc_pc].copy()

# iterate over the dataframe row by row and set version
prediction = { "mean": 350, "std": 0, "min": 350, "max": 350 }
prediction_history = { "mean": 1000, "std": 0, "min": 1000, "max": 1000 }

meta = {
    "current_version": "transcoder-image-1-con",
    "current_version_history_grouped": "transcoder-image-1-con",
    "recent_history": prediction_history
}


supported_versions = get_supported_versions(
    prediction=prediction, versions=PD["versions"])

decision_matrix_df = build_decision_matrix(
    prediction=prediction, meta=meta, versions=supported_versions)

# weights = WEIGHTS
weights = {
    "negative": {
        "cost": 9,
        "over_provision": 9,
        "overhead": 5
    },
    "positive": {
        "support_deviation": 4,
        "same_version": 5,
        "support_max": 1,
        "support_recent_history": 1
    }
}

# Negative
cost = weights["negative"]["cost"]
over_provision = weights["negative"]["over_provision"]
overhead = weights["negative"]["overhead"]
support_deviation = weights["positive"]['support_deviation']
same_version = weights["positive"]['same_version']
support_max = weights["positive"]['support_max']
support_recent_history = weights["positive"]['support_recent_history']

c_cost = MIN
c_over_provision = MIN
c_overhead = MIN
c_support_deviation = MAX
c_same_version = MAX
c_support_max = MAX
c_support_recent_history = MAX


# WEIGHTS --> [cost, support_deviation, over_provision, same_version, overhead, support_max, support_recent_history]
weights = [cost, support_deviation, over_provision,
                same_version, overhead, support_max, support_recent_history]

criteria = [c_cost, c_support_deviation, c_over_provision,
                c_same_version, c_overhead, c_support_max, c_support_recent_history]

list(decision_matrix_df.index)

get_policy_decision_mcda

print("WSM")
data = Data(decision_matrix_df.values, criteria,
            weights=weights,
            anames=decision_matrix_df.index,
            cnames=list(decision_matrix_df.columns))

dm = simple.WeightedSum()
dec = dm.decide(data)
print(data.anames[dec.best_alternative_])

print("WPM")
data = Data(decision_matrix_df.values, criteria,
            weights=weights,
            anames=decision_matrix_df.index,
            cnames=list(decision_matrix_df.columns))

dm = simple.WeightedProduct()
dec = dm.decide(data)
print(data.anames[dec.best_alternative_])

print("TOPSIS")
data = Data(decision_matrix_df.values, criteria,
            weights=weights,
            anames=decision_matrix_df.index,
            cnames=list(decision_matrix_df.columns))

dm = closeness.TOPSIS()
dec = dm.decide(data)
print(data.anames[dec.best_alternative_])

print("Ideal:", dec.e_.ideal)
print("Anti-Ideal:", dec.e_.anti_ideal)
print("Closeness:", dec.e_.closeness)
# %%


    

# %%

print("Took: {}".format((time.time() - START_TIME)/60))


# %%
