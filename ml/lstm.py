# https://www.section.io/engineering-education/stock-price-prediction-using-python/
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from keras.models import Sequential, load_model
from keras.layers import LSTM, Dense, Dropout 
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
sys.path.append(os.path.abspath("..\Database"))
from backtest_db import backtesting_db

class lstm:
    def __init__(self, api_key:str, api_secret:str, coin_symb_list, coin_usdt_list, start_date_list, end_date_list, db_time_interval:int, time_interval, learn_size, horizon, epochs, units_list=[96,96,96,96]):
        self.api_key = api_key
        self.api_secret = api_secret
        self.coin_symb_list = coin_symb_list
        self.coin_usdt_list = coin_usdt_list
        self.start_date_list = start_date_list
        self.end_date_list = end_date_list
        self.db_time_interval = db_time_interval
        self.time_interval = time_interval
        self.units_list = units_list
        self.input_size = learn_size #TODO check
        self.epochs = epochs
        self.model = self.build_model(units_list=self.units_list, input_size=self.input_size)
        self.learn_size = learn_size
        self.horizon = horizon
        self.scaler = MinMaxScaler(feature_range=(0,1))

    def training_testing(self, train_size = 0.8):
        feature_train_list, target_train_list, feature_test_list, target_test_list = [], [], [], []
        for i in range(len(self.coin_usdt_list)):
            untransformed_data = self.get_data(self.coin_usdt_list[i],self.start_date_list[i], self.end_date_list[i]) # should be a timeseries
            train_data, test_data = self.transform_data(untransformed_data, train_size) #TODO check train_size
            feature_train, target_train = self.create_datasets(train_data,self.learn_size,self.horizon)
            feature_test, target_test = self.create_datasets(test_data,self.learn_size,self.horizon)
            feature_train_list.append(feature_train)
            target_train_list.append(target_train)
            feature_test_list.append(feature_test)
            target_test_list.append(target_test)
        if len(feature_train_list) > 1:
            raise ValueError('pas encore codé pour plusieurs symboles')
        self.train(feature_train_list[0], target_train_list[0])
        predictions, target = self.test(feature_test_list[0],target_test_list[0])
        self.visualize(predictions, target)
        pass

    def train(self,feature,target,callback_patience=2, save=False): # inplace, modifies self.model
        callback = tf.keras.callbacks.EarlyStopping(monitor='loss', patience=callback_patience)
        self.model.fit(feature,target, epochs=self.epochs, batch_size=32, callbacks=[callback]) #TODO à thuner
        if save:
            self.model.save(f'lstm_{self.coin_symb_list[0]}.h5') #can be opened with load_model

    def test(self,feature, target): # testing and visualizing
        predictions = self.model.predict(feature)
        predictions = self.scaler.inverse_transform(predictions)
        target_rescaled = self.scaler.inverse_transform(target.reshape(-1,1)) #TODO check reshape
        return predictions, target_rescaled

    def get_data(self, coin_usdt_symb, start_date, end_date):
        bdb = backtesting_db(api_key=self.api_key, api_secret=self.api_secret, coin_usdt_symb = coin_usdt_symb, db_time_interval = self.db_time_interval, start_date=start_date, end_date=end_date)
        data = bdb.get_data()
        return data['Price'].values


    def transform_data(self,timeseries, train_size): # timeseries : prices df
        train_limit = int(timeseries.shape[0] * train_size)
        train_data = timeseries[:train_limit]
        test_data =  timeseries[train_limit:]
        # rescaling to get 2D (later we will go to 3D)
        train_data = train_data.reshape(-1,1)
        test_data = test_data.reshape(-1,1) #TODO test
        # normalizing with windows may be better
        train_data = self.scaler.fit_transform(train_data) # fiting on training data
        test_data = self.scaler.transform(test_data)
        return train_data, test_data # both 2D

    def create_datasets(self,timeseries, learn_size, horizon): # learn size: size of input feature # horizon with respect to time interval # df should be 2D (even if 1 column)
        feature, target = [],[]
        for i in range(learn_size, timeseries.shape[0] - horizon):
            feature.append(timeseries[i-learn_size:i,0])
            target.append(timeseries[i+ horizon,0])
        feature = np.array(feature)
        target = np.array(target)
        # feature needs to be 3D
        feature = np.reshape(feature,(feature.shape[0], feature.shape[1],1))
        return feature, target # feature 3D


    def build_model(self, units_list, input_size, dropout=0.2):
        model = Sequential()
        model.add(LSTM(units=units_list[0], return_sequences=True, input_shape=(input_size,1)))
        model.add(Dropout(dropout))
        for i in range(1,len(units_list)-1):
            model.add(LSTM(units=units_list[i],return_sequences=True))
            model.add(Dropout(dropout))
        model.add(LSTM(units=units_list[-1]))
        model.add(Dropout(dropout))
        model.add(Dense(units=1))
        model.compile(loss='mean_squared_error', optimizer='adam')
        return model

    def visualize(self, predictions, target):
        fig, ax = plt.subplots(figsize=(16,8))
        ax.set_facecolor('#000041')
        ax.plot(target, color='red',label='Original price')
        ax.plot(predictions, color='cyan', label='Predicted price')
        plt.legend()
        # plt.show()


    