import pandas as pd
import numpy as np

from sklearn import preprocessing
_SCORE_MIN, _SCORE_MAX = 1, 5

from skcriteria import Data, MIN, MAX
from skcriteria.madm import closeness, simple

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
                _max_datarate_version = { _vm_type_key: { _vm_version_key : _vm_version_value } }

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
            # if _vm_version_value['max_data_rate'] >= (meta["recent_history"]["mean"]):
            #     _decision_matrix[_vm_type_key][_vm_version_key]["support_recent_history"] = 5
            # else:
                # _decision_matrix[_vm_type_key][_vm_version_key]["support_recent_history"] = 1
            # FIXME: add support for recent history
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
Get policy decision given decision matrix and weights using MCDA
'''
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
        dm = closeness.TOPSIS(mnorm="sum")

    dec = dm.decide(data)

    # print(dec.e_.points)
    return data.anames[dec.best_alternative_]


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

    # WEIGHTS --> [cost, over_provision, overhead, support_deviation, same_version]
    weights_row = [cost, over_provision, overhead, support_deviation, same_version]

    for index_label, row_series in decision_matrix.iterrows():
        _row = np.array([row_series.cost, row_series.over_provision, row_series.overhead, row_series.support_deviation, row_series.same_version])

        decision_matrix.at[index_label , 'score'] = np.dot(np.array(weights_row), _row)

    _version = decision_matrix[decision_matrix.score == decision_matrix.score.max()].index[0]
    return _version

'''
Find the version with least cost
'''
def find_cheapest_version(versions):
    _cost = None

    for _vm_type_key, _vm_type_value in versions.items():
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