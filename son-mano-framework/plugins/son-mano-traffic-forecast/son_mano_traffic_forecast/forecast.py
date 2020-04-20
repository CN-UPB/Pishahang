"""
Copyright (c) 2015 SONATA-NFV
ALL RIGHTS RESERVED.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.
This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).a
"""

import logging
import yaml
import time
import os
import requests
import copy
import uuid
import json
import threading
import sys
import csv
import traceback
# import concurrent.futures as pool

# DL
import numpy as np
import tensorflow as tf
from tensorflow import keras
import pandas as pd
# import seaborn as sns
from pylab import rcParams
import matplotlib.pyplot as plt
from matplotlib import rc

from pathlib import Path

from sklearn.preprocessing import MinMaxScaler

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Dropout
from tensorflow.keras.models import load_model

from sonmanobase.plugin import ManoBasePlugin

try:
    from son_mano_traffic_forecast import helpers as tools
except:
    import helpers as tools

import os
import psutil
process = psutil.Process(os.getpid())
import multiprocessing

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("plugin:tfp")
LOG.setLevel(logging.INFO)

DEBUG_MODE = False

class TFPlugin(ManoBasePlugin):
    """
    This class implements the Traffic Forecasting Plugin.
    """

    def __init__(self,
                 auto_register=True,
                 wait_for_registration=True,
                 start_running=True):
        """
        Initialize class and son-mano-base.plugin.BasePlugin class.
        This will automatically connect to the broker, contact the
        plugin manager, and self-register this plugin to the plugin
        manager.

        After the connection and registration procedures are done, the
        'on_lifecycle_start' method is called.
        :return:
        """

        # call super class (will automatically connect to
        # broker and register the Traffic Forecasting plugin to the plugin manger)
        ver = "0.1-dev"
        des = "This is the Traffic Forecasting plugin"

        Path("models").mkdir(parents=True, exist_ok=True)

        self.active_services = {}
        self.scaler = MinMaxScaler(feature_range = (0, 1))

        super(self.__class__, self).__init__(version=ver,
                                             description=des,
                                             auto_register=auto_register,
                                             wait_for_registration=wait_for_registration,
                                             start_running=start_running)

    def __del__(self):
        """
        Destroy Traffic Forecasting plugin instance. De-register. Disconnect.
        :return:
        """
        super(self.__class__, self).__del__()

    def declare_subscriptions(self):
        """
        Declare topics that Traffic Forecasting Plugin subscribes on.
        """
        # We have to call our super class here
        super(self.__class__, self).declare_subscriptions()

        # The topic on which deploy requests are posted.
        self.topic = 'mano.service.forecast'
        self.manoconn.subscribe(self.forecast_request, self.topic)

        LOG.info("Subscribed to topic: " + str(self.topic))

    def on_lifecycle_start(self, ch, mthd, prop, msg):
        """
        This event is called when the plugin has successfully registered itself
        to the plugin manager and received its lifecycle.start event from the
        plugin manager. The plugin is expected to do its work after this event.

        :param ch: RabbitMQ channel
        :param method: RabbitMQ method
        :param properties: RabbitMQ properties
        :param message: RabbitMQ message content
        :return:
        """
        super(self.__class__, self).on_lifecycle_start(ch, mthd, prop, msg)
        LOG.info("Traffic Forecasting plugin started and operational.")
        # self.forecasting_thread("test")

    def deregister(self):
        """
        Send a deregister request to the plugin manager.
        """
        LOG.info('Deregistering Traffic Forecasting plugin with uuid ' + str(self.uuid))
        message = {"uuid": self.uuid}
        self.manoconn.notify("platform.management.plugin.deregister",
                             json.dumps(message))
        os._exit(0)

    def on_registration_ok(self):
        """
        This method is called when the Traffic Forecasting plugin
        is registered to the plugin mananger
        """
        super(self.__class__, self).on_registration_ok()
        LOG.debug("Received registration ok event.")

    def remove_empty_values(self, line):
        """
        remove empty values (from multiple delimiters in a row)
        :param line: Receives the Line
        :return: sends back after removing the empty value
        """
        result = []
        for i in range(len(line)):
            if line[i] != "":
                result.append(line[i])
        return result


##########################
# TFP
##########################
    def forecast_request(self, ch, method, prop, payload):
        """
        This method handles a Forecasting request
        """
        if prop.app_id == self.name:
            return

        content = yaml.load(payload)
        serv_id = content['serv_id']

        LOG.info("Forecast request for service: " + serv_id)
        # LOG.info(content)

        if content['request_type'] == "start_forecast_thread":
            try:
                self.active_services[serv_id] = content
                self.active_services[serv_id]["MODEL_NAME"] = "{}_model.h5".format(serv_id)
                self.active_services[serv_id]["predicting"] = False
                self.active_services[serv_id]["last_seen_until"] = 0

                # LOG.info("EXP: Switch Time - {}".format(time.time() - self.EXP_REQ_TIME))
            
                # Start forecasting thread
                self.forecasting_thread(serv_id)
            except Exception as e:
                LOG.error("Error")
                LOG.error(e)
                track = traceback.format_exc()
                LOG.error(track)

        elif content['request_type'] == "stop_forecast_thread":
            self.active_services.pop(serv_id, None)
            LOG.info("Forecasting stopped")

        elif content['request_type'] == "get_prediction":
            LOG.info("Get prediction")
            req_serv_id = content['serv_id']

            self.process_prediction_request(req_serv_id, prop)

        else:
            LOG.info("Request type not suppoted")

    @tools.run_async
    def process_prediction_request(self, req_serv_id, prop):
            manager = multiprocessing.Manager()
            return_dict = manager.dict()

            self.active_services[req_serv_id]['predicting'] = True
            p = multiprocessing.Process(target=self.get_prediction_next_time_block, args=(req_serv_id, return_dict))
            p.start()
            p_killed = False
            while(p.is_alive()):
                # LOG.info("Predicting..." + req_serv_id)
                if req_serv_id in self.active_services:
                    # LOG.info("Still active..." + req_serv_id)
                    pass
                else:
                    LOG.info("Killing training..." + req_serv_id)
                    p.terminate()
                    p_killed = True

                time.sleep(1)

            if not p_killed:
                # p.join()
                self.active_services[req_serv_id]['predicting'] = False

                prediction = return_dict['prediction']

                # prediction = self.get_prediction_next_time_block(req_serv_id)

                response = {
                    'serv_id': req_serv_id,
                    'prediction': prediction
                    }

                LOG.info(response)

                self.manoconn.notify(self.topic,
                                    yaml.dump(response),
                                    correlation_id=prop.correlation_id)

    def get_prediction_next_time_block(self, serv_id, return_dict):
        try:
            training_config = {}
            training_config['MODEL_NAME'] = self.active_services[serv_id]["MODEL_NAME"]
            training_config['look_ahead_time_block'] = self.active_services[serv_id]['policy']['look_ahead_time_block']
            training_config['history_time_block'] = self.active_services[serv_id]['policy']['history_time_block']
            training_config['time_block'] = self.active_services[serv_id]['policy']['time_block']
            training_config['traffic_direction'] = 'received'
            # training_config['avg_sec'] = self.active_services[serv_id]["MODEL_NAME"]

            # Fetch data from netdata
            # FIXME: need to fix how charts are fetched from netdata
            _instance_meta = self.active_services[serv_id]['ports']
            _mon_parameters = self.active_services[serv_id]['monitoring_parameters']
            vim_endpoint = self.active_services[serv_id]['vim_endpoint']

            _charts = tools.get_netdata_charts(_instance_meta['uid'], vim_endpoint, _mon_parameters)
            charts = _charts            
            # vim_endpoint = self.active_services[serv_id]['vim_endpoint']
            # charts = self.active_services[serv_id]['charts']
            
            _look_back_time = (training_config['time_block'] * training_config['history_time_block']) * -1

            _data_frame_test = self.fetch_data(charts, vim_endpoint, training_config['time_block'], look_back_time=_look_back_time)
            # _data_frame_test = _data_frame_test.iloc[-3:]
            test_X = self.prepare_data(_data_frame_test, training_config, for_prediction=True)

            LOG.info("Prediction")

            _prediction = self.predict_using_lstm(test_X, serv_id)

            prediction_metrics = {
                "mean": float(np.mean(_prediction)),
                "std": float(np.std(_prediction)),
                "max": float(np.max(_prediction)),
                "min": float(np.min(_prediction))
            }

            # LOG.info(_prediction[0])
            # LOG.info(prediction_metrics)

            # self.active_services[serv_id]['predicting'] = False

            return_dict['prediction'] = prediction_metrics
            return prediction_metrics

        except Exception as e:
            LOG.error("Error")
            LOG.error(e)
            track = traceback.format_exc()
            LOG.error(track)
            return_dict['prediction'] = None
            return None

    @tools.run_async
    def forecasting_thread(self, serv_id):
        LOG.info("### Setting up forecasting thread: " + serv_id)
        LOG.info("### waiting for initial period")
        if DEBUG_MODE:
            while(True):
                try:
                    LOG.info("Monitoring Thread " + serv_id)

                    # self.active_services[serv_id] = {}
                    # self.active_services[serv_id]['policy'] = {}                    
                    # self.active_services[serv_id]["MODEL_NAME"] = "{}_model.h5".format(serv_id)
                    # self.active_services[serv_id]['policy']['look_ahead_time_block'] = 3
                    # self.active_services[serv_id]['policy']['history_time_block'] = 30
                    # self.active_services[serv_id]['policy']['time_block'] = 1

                    # training_config = {}
                    # training_config['MODEL_NAME'] = "{}_model.h5".format(serv_id)
                    # training_config['traffic_direction'] = 'received'

                    # training_config['look_ahead_time_block'] = 3
                    # training_config['history_time_block'] = 30
                    # training_config['time_block'] = 1
                    # # training_config['avg_sec'] = self.active_services[serv_id]["MODEL_NAME"]

                    # # Fetch data from netdata
                    # vim_endpoint = "vimdemo1.cs.upb.de"
                    # charts = ["cgroup_qemu_qemu_127_instance_0000007f.net_tap0c32c278_4e"]

                    # self.active_services[serv_id]["vim_endpoint"] = vim_endpoint
                    # self.active_services[serv_id]["charts"] = charts
                    # # 7 days = 604800
                    # avg_sec = 604800
                    # time_block = 10
                    # look_back_time = 300

                    # # _data = tools.get_netdata_charts_instance(charts,
                    # #                                             vim_endpoint)

                    # start_time = time.time()

                    # _data_frame = self.fetch_data(charts, vim_endpoint, training_config['time_block'], look_back_time)

                    # X, Y = self.prepare_data(_data_frame, training_config)
                    # self.lstm_training(X, Y, training_config)
            
                    # self.safely_rename_model(serv_id)

                    # # LOG.info(json.dumps(_metrics, indent=4, sort_keys=True))
                    # # self.predict_using_lstm(X)
                    # LOG.info(time.time()-start_time)

                    # LOG.info(json.dumps(_metrics, indent=4, sort_keys=True))

                    # LOG.info("### net ###")
                    # LOG.info(_metrics["net"])

                except Exception as e:
                    LOG.error("Error")
                    LOG.error(e)
                    track = traceback.format_exc()
                    LOG.error(track)

                time.sleep(10)
                LOG.info("PREDICTING NOW")

                # _data_frame_test = self.fetch_data(charts, vim_endpoint, training_config['time_block'])
                # _data_frame_test = _data_frame_test.iloc[-100:]
                # test_X, test_Y = self.prepare_data(_data_frame_test, training_config)

                # self.predict_using_lstm(test_X, serv_id)
                self.get_prediction_next_time_block(serv_id)

                time.sleep(10)

        else:
            time.sleep(self.active_services[serv_id]['policy']['initial_observation_period'])
            while(serv_id in self.active_services):
                try:
                    LOG.info("Forecast Thread " + serv_id)

                    training_config = {}
                    training_config['MODEL_NAME'] = self.active_services[serv_id]["MODEL_NAME"]
                    training_config['look_ahead_time_block'] = self.active_services[serv_id]['policy']['look_ahead_time_block']
                    training_config['history_time_block'] = self.active_services[serv_id]['policy']['history_time_block']
                    training_config['time_block'] = self.active_services[serv_id]['policy']['time_block']
                    training_config['training_history_days'] = self.active_services[serv_id]['policy']['training_history_days']
                    
                    training_config['traffic_direction'] = 'received'
                    # training_config['avg_sec'] = self.active_services[serv_id]["MODEL_NAME"]

                    # Fetch data from netdata
                    # FIXME: need to fix how charts are fetched from netdata
                    _instance_meta = self.active_services[serv_id]['ports']
                    _mon_parameters = self.active_services[serv_id]['monitoring_parameters']
                    vim_endpoint = self.active_services[serv_id]['vim_endpoint']

                    _charts = tools.get_netdata_charts(_instance_meta['uid'], vim_endpoint, _mon_parameters)
                    charts = _charts

                    # training_history_days = int(training_config['training_history_days'] * 24 * 60 * 60) 

                    # if training_history_days > 0:
                    #     _last_seen_until =  self.active_services[serv_id]["last_seen_until"]

                    #     if _last_seen_until < training_history_days:
                    #         look_back_time = _last_seen_until
                    #     else:
                    #         look_back_time = training_history_days

                    # else:

                    look_back_time = self.active_services[serv_id]["last_seen_until"]

                    # 7 days = 604800

                    # _data = tools.get_netdata_charts_instance(charts,
                    #                                             vim_endpoint)

                    start_time = time.time()
                    LOG.info("#### Starting Training \n\n\n")  # in bytes 

                    _data_frame = self.fetch_data(charts, vim_endpoint, training_config['time_block'], look_back_time=look_back_time)

                    new_look_back_time = int(_data_frame.index[-1])

                    X, Y = self.prepare_data(_data_frame, training_config)

                    # self.lstm_training(X, Y, training_config)

                    p = multiprocessing.Process(target=self.lstm_training, args=(X, Y, training_config))
                    p.start()

                    p_killed = False
                    while(p.is_alive()):
                        # LOG.info("Training..." + serv_id)
                        if serv_id in self.active_services:
                            # LOG.info("Still active..." + serv_id)
                            pass
                        else:
                            LOG.info("Killing training..." + serv_id)
                            p.terminate()
                            p_killed = True
                        time.sleep(1)
                    # p.join()

                    if not p_killed:
                        self.safely_rename_model(serv_id)

                        self.active_services[serv_id]["last_seen_until"] = new_look_back_time

                        LOG.info(time.time()-start_time)

                        del _data_frame, X, Y

                        # self.get_prediction_next_time_block(serv_id)
                        LOG.info("\n\n\n")  # in bytes 
                        LOG.info(process.memory_info().rss)  # in bytes 


                        time.sleep(self.active_services[serv_id]['policy']['forecast_training_frequency'])
                except Exception as e:
                    LOG.error("Error")
                    LOG.error(e)
                    track = traceback.format_exc()
                    LOG.error(track)
                    time.sleep(10)


        LOG.info("### Stopping forecasting thread for: " + serv_id)

    # def create_lstm_dataset(self, X, y, time_steps=1):
    #     Xs, ys = [], []
    #     for i in range(len(X) - time_steps):
    #         v = X.iloc[i:(i + time_steps)].values
    #         Xs.append(v)        
    #         ys.append(y.iloc[i + time_steps])
    #     return np.array(Xs), np.array(ys)

    def safely_rename_model(self, serv_id):
        while(self.active_services[serv_id]['predicting']):
            time.sleep(0.5)
            LOG.info("### Waiting to rename model " + serv_id)
        
        MODEL_NAME = self.active_services[serv_id]["MODEL_NAME"]
        os.rename("models/safe_{}".format(MODEL_NAME), "models/{}".format(MODEL_NAME)) 
        LOG.info("### Model renamed" + serv_id)


    # split a univariate sequence into samples
    def create_lstm_dataset(self, sequence, n_steps_in, n_steps_out):
        X, y = list(), list()
        for i in range(len(sequence)):
            # find the end of this pattern
            end_ix = i + n_steps_in
            out_end_ix = end_ix + n_steps_out
            # check if we are beyond the sequence
            if out_end_ix > len(sequence):
                break
            # gather input and output parts of the pattern
            seq_x, seq_y = sequence[i:end_ix], sequence[end_ix:out_end_ix]
            X.append(seq_x)
            y.append(seq_y)
        return np.array(X), np.array(y)

    def create_lstm_predict_dataset(self, sequence, n_steps_in, n_steps_out):
        X = list()
        seq_x = sequence[:n_steps_in]
        X.append(seq_x)
        return np.array(X)

    def fetch_data(self, charts, vim_endpoint, time_block, look_back_time=0):
        # http://vimdemo1.cs.upb.de:19999/api/v1/data?chart=cgroup_qemu_qemu_127_instance_0000007f.net_tap0c32c278_4e&gtime=60
        _data = tools.get_netdata_charts_instance(charts,
                                                    vim_endpoint, avg_sec=look_back_time, gtime=time_block)

        train = pd.DataFrame(_data['net']['data'], columns=_data['net']['labels'])

        train = train.set_index("time")

        return train

    def prepare_data(self, raw_data, training_config, for_prediction=False):
        history_time_block = training_config['history_time_block']
        look_ahead_time_block = training_config['look_ahead_time_block']

        traffic_direction = training_config['traffic_direction']

        # raw_data = self.fetch_data()

        traffic_training_processed_complete = raw_data[[traffic_direction]]

        traffic_training_scaled_complete = self.scaler.fit_transform(traffic_training_processed_complete)

        dataset = pd.DataFrame(traffic_training_scaled_complete, columns=[traffic_direction])
        # LOG.info(dataset.head(5))

        n_steps_in, n_steps_out = history_time_block, look_ahead_time_block
        n_features = 1

        if for_prediction:

            X_pred = self.create_lstm_predict_dataset(dataset[traffic_direction], n_steps_in, n_steps_out)
            X_pred = X_pred.reshape((X_pred.shape[0], X_pred.shape[1], n_features))
            return X_pred

        else:
            # split into samples
            X_train, y_train = self.create_lstm_dataset(dataset[traffic_direction], n_steps_in, n_steps_out)

            # reshape from [samples, timesteps] into [samples, timesteps, features]
            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], n_features))

            # LOG.info(str(X_train.shape), str(y_train.shape))

            return X_train, y_train

    def lstm_training(self, X_train, y_train, training_config):
        # TODO: Fetch from policy 
        EPOCHS = 5
        BATCH_SIZE = 32
        MODEL_NAME = training_config['MODEL_NAME']
        look_ahead_time_block = training_config['look_ahead_time_block']

        if os.path.isfile("models/{}".format(MODEL_NAME)):
            # load model
            LOG.info("Iterative learning - loading model")
            model = load_model("models/{}".format(MODEL_NAME))
        else:
            LOG.info("Creating model first time")

            model = keras.Sequential()
            # model.add(keras.layers.LSTM(128, input_shape=(X_train.shape[1], X_train.shape[2])))
            # model.add(keras.layers.Dense(1))

            model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
            model.add(Dropout(0.2))

            model.add(LSTM(units=50, return_sequences=True))
            model.add(Dropout(0.2))

            model.add(LSTM(units=50, return_sequences=True))
            model.add(Dropout(0.2))

            model.add(LSTM(units=50))
            model.add(Dropout(0.2))

            model.add(Dense(units = look_ahead_time_block))

            # model.compile(loss='mean_squared_error', optimizer=keras.optimizers.Adam(0.001))
            model.compile(optimizer=keras.optimizers.Adam(0.001), loss = 'mean_squared_error')
            
        history = model.fit(
            X_train, y_train, 
            epochs=EPOCHS, 
            batch_size=BATCH_SIZE, 
            validation_split=0.1, 
            verbose=1
        )

        # LOG.info(history.history)

        model.save("models/safe_{}".format(MODEL_NAME))

        del model, history, X_train, y_train
        
    def predict_using_lstm(self, input_data, serv_id):
        # TODO: Import model here
        MODEL_NAME = self.active_services[serv_id]["MODEL_NAME"]

        model = load_model("models/{}".format(MODEL_NAME))

        y_pred = model.predict(input_data)
        y_pred = self.scaler.inverse_transform(y_pred)

        LOG.info(y_pred)

        return y_pred

    def tfp_request(self, ch, method, prop, payload):
        """
        This method handles a placement request
        """

        if prop.app_id == self.name:
            return

        # TODO: Receive request and create new prediction thread and state

    def tfp_predict(self, ch, method, prop, payload):
        """
        This method handles a placement request
        """

        if prop.app_id == self.name:
            return

        # TODO: use the most recent model from the training thread and return prediction

        content = yaml.load(payload)


def main():
    """
    Entry point to start plugin.
    :return:
    """
    # reduce messaging log level to have a nicer output for this plugin
    logging.getLogger("son-mano-base:messaging").setLevel(logging.INFO)
    logging.getLogger("son-mano-base:plugin").setLevel(logging.INFO)
    tfp = TFPlugin()
    LOG.info("SSUP")

if __name__ == '__main__':
    main()
