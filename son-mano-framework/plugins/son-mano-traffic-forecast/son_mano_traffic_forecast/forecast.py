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
        topic = 'mano.service.forecast'
        self.manoconn.subscribe(self.forecast_request, topic)

        LOG.info("Subscribed to topic: " + str(topic))

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
        LOG.info(content)

        if content['request_type'] == "start_forecast_thread":
            self.active_services[serv_id] = content
            self.active_services[serv_id]["MODEL_NAME"] = "{}_model.h5".format(serv_id)

            # LOG.info("EXP: Switch Time - {}".format(time.time() - self.EXP_REQ_TIME))
           
            # Start forecasting thread
            self.forecasting_thread(serv_id)

        elif content['request_type'] == "stop_forecast_thread":
            self.active_services.pop(serv_id, None)
            LOG.info("Forecasting stopped")

        elif content['request_type'] == "get_prediction":
            LOG.info("Get prediction")

            self.active_services[serv_id] = content
            self.active_services[serv_id]["MODEL_NAME"] = "{}_model.h5".format(serv_id)

            self.get_prediction_next_time_block(serv_id)
        # TODO: Add URL Switching for URL version switching 
        # elif content['request_type'] == "STOP":
        #     self.active_services.pop(serv_id, None)
        #     LOG.info("Forecasting stopped")

        else:
            LOG.info("Request type not suppoted")

    def get_prediction_next_time_block(self, serv_id):

        training_config = {}
        training_config['MODEL_NAME'] = self.active_services[serv_id]["MODEL_NAME"]
        training_config['time_steps'] = self.active_services[serv_id]['policy']['look_ahead_time_block']
        training_config['traffic_direction'] = 'received'
        # training_config['avg_sec'] = self.active_services[serv_id]["MODEL_NAME"]
        training_config['group_time'] = self.active_services[serv_id]['policy']['monitoring_config']['average_range']

        # Fetch data from netdata
        vim_endpoint = self.active_services[serv_id]['vim_endpoint']
        charts = self.active_services[serv_id]['charts']
        
        _look_back_time = (training_config['group_time'] * training_config['time_steps']) + 1
        _data_frame_test = self.fetch_data(charts, vim_endpoint, training_config['group_time'], look_back_time=_look_back_time)
        _data_frame_test = _data_frame_test.iloc[-3:]
        test_X, test_Y = self.prepare_data(_data_frame_test, training_config)

        LOG.info("Prediction")
        self.predict_using_lstm(test_X, serv_id)

    @tools.run_async
    def forecasting_thread(self, serv_id):
        LOG.info("### Setting up forecasting thread: " + serv_id)
        LOG.info("### waiting for initial period")
        time.sleep(self.active_services[serv_id]['policy']['initial_observation_period'])
        if DEBUG_MODE:
            while(True):
                try:
                    LOG.info("Monitoring Thread " + serv_id)

                    training_config = {}
                    training_config['MODEL_NAME'] = self.active_services[serv_id]["MODEL_NAME"]
                    training_config['time_steps'] = 10
                    training_config['traffic_direction'] = 'received'

                    # Fetch data from netdata
                    vim_endpoint = "vimdemo1.cs.upb.de"
                    charts = ["cgroup_qemu_qemu_127_instance_0000007f.net_tap0c32c278_4e"]
                    # 7 days = 604800
                    avg_sec = 604800
                    group_time = 10

                    # _data = tools.get_netdata_charts_instance(charts,
                    #                                             vim_endpoint)


                    _data_frame = self.fetch_data(charts, vim_endpoint, training_config['group_time'])

                    X, Y = self.prepare_data(_data_frame, training_config)
                    self.lstm_training(X, Y, training_config)
                    # LOG.info(json.dumps(_metrics, indent=4, sort_keys=True))
                    start_time = time.time()
                    # self.predict_using_lstm(X)
                    LOG.info(time.time()-start_time)

                    # LOG.info(json.dumps(_metrics, indent=4, sort_keys=True))

                    # LOG.info("### net ###")
                    # LOG.info(_metrics["net"])

                except Exception as e:
                    LOG.error("Error")
                    LOG.error(e)
                    track = traceback.format_exc()
                    LOG.error(track)

                time.sleep(30)

                _data_frame_test = self.fetch_data(charts, vim_endpoint, training_config['group_time'])
                _data_frame_test = _data_frame_test.iloc[-20:]
                test_X, test_Y = self.prepare_data(_data_frame_test, training_config)

                self.predict_using_lstm(test_X)

        else:
            while(serv_id in self.active_services):
                try:
                    LOG.info("Forecast Thread " + serv_id)

                    training_config = {}
                    training_config['MODEL_NAME'] = self.active_services[serv_id]["MODEL_NAME"]
                    training_config['time_steps'] = self.active_services[serv_id]['policy']['look_ahead_time_block']
                    training_config['observation_time_block'] = self.active_services[serv_id]['policy']['observation_time_block']
                    training_config['traffic_direction'] = 'received'
                    # training_config['avg_sec'] = self.active_services[serv_id]["MODEL_NAME"]
                    training_config['group_time'] = self.active_services[serv_id]['policy']['monitoring_config']['average_range']

                    # Fetch data from netdata
                    vim_endpoint = self.active_services[serv_id]['vim_endpoint']
                    charts = self.active_services[serv_id]['charts']

                    # 7 days = 604800

                    # _data = tools.get_netdata_charts_instance(charts,
                    #                                             vim_endpoint)

                    start_time = time.time()

                    _data_frame = self.fetch_data(charts, vim_endpoint, training_config['group_time'])

                    X, Y = self.prepare_data(_data_frame, training_config)
                    self.lstm_training(X, Y, training_config)
                    LOG.info(time.time()-start_time)

                    self.get_prediction_next_time_block(serv_id)

                    time.sleep(self.active_services[serv_id]['policy']['forecast_training_frequency'])
                except Exception as e:
                    LOG.error("Error")
                    LOG.error(e)
                    track = traceback.format_exc()
                    LOG.error(track)
                    time.sleep(30)


        LOG.info("### Stopping forecasting thread for: " + serv_id)

    def create_lstm_dataset(self, X, y, time_steps=1):
        Xs, ys = [], []
        for i in range(len(X) - time_steps):
            v = X.iloc[i:(i + time_steps)].values
            Xs.append(v)        
            ys.append(y.iloc[i + time_steps])
        return np.array(Xs), np.array(ys)

    def fetch_data(self, charts, vim_endpoint, group_time, look_back_time=0):
        # http://vimdemo1.cs.upb.de:19999/api/v1/data?chart=cgroup_qemu_qemu_127_instance_0000007f.net_tap0c32c278_4e&gtime=60
        _data = tools.get_netdata_charts_instance(charts,
                                                    vim_endpoint, avg_sec=look_back_time, gtime=group_time)

        train = pd.DataFrame(_data['net']['data'], columns=_data['net']['labels'])

        train = train.set_index("time")

        return train

    def prepare_data(self, raw_data, training_config):
        time_steps = training_config['time_steps']
        traffic_direction = training_config['traffic_direction']

        # raw_data = self.fetch_data()

        traffic_training_processed_complete = raw_data[[traffic_direction]]

        traffic_training_scaled_complete = self.scaler.fit_transform(traffic_training_processed_complete)

        dataset = pd.DataFrame(traffic_training_scaled_complete, columns=[traffic_direction])
        # LOG.info(dataset.head(5))

        # reshape to [samples, time_steps, n_features]
        X_train, y_train = self.create_lstm_dataset(dataset, dataset[traffic_direction], time_steps)

        # LOG.info(str(X_train.shape), str(y_train.shape))

        return X_train, y_train

    def lstm_training(self, X_train, y_train, training_config):
        EPOCHS = 5
        BATCH_SIZE = 32
        MODEL_NAME = training_config['MODEL_NAME']

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

        model.add(Dense(units = 1))

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

        model.save("models/{}".format(MODEL_NAME))

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
