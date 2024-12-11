import pandas as pd
import os
import sqlalchemy
from binance.client import Client
from binance import BinanceSocketManager
from datetime import datetime
import websocket
import json
import multiprocessing
# ref: https://www.youtube.com/watch?v=rc_Y6rdBqXM

class live_db(): # to test: run the run_live_db fun
    def __init__(self, coin_usdt_symb:str, db_name:str, stream_str:str='@kline_1m'):
        self.coin_usdt_symb = coin_usdt_symb
        self.stream_str = stream_str
        self.db_name = db_name
        self.engine = self.create_engine()
        self.ws = self.create_websocket(self.coin_usdt_symb, self.on_open, self.on_close, self.on_message, self.stream_str)

    def run_ws(self, ws=None):
        if ws == None:
            ws = self.ws
        ws.run_forever()

    def create_engine(self):
        engine_url = f"sqlite:///..\Dbs\{self.db_name}stream.db"  # to change ?
        print(f'engine path : {engine_url}')
        engine = sqlalchemy.create_engine(engine_url)
        return engine
    
    def on_open(self, ws):
        print('ws open')

    def on_close(self, ws, close_status_code, close_msg):
        print("on_close args:")
        if close_status_code or close_msg:
            print("close status code: " + str(close_status_code))
            print("close message: " + str(close_msg))
        self.run_ws()

    def on_message(self, ws, message):
        message = json.loads(message)
        candle = message['k']
        is_candle_closed = candle['x']
        if is_candle_closed:
            df = self.create_df(symbol=message['s'], time=message['E'], close=candle['c'])
            df.to_sql(self.coin_usdt_symb, self.engine, if_exists='append', index = False)
        # df = self.create_df(symbol=message['s'], time=message['E'], close=candle['c'])
        # df.to_sql(self.coin_usdt_symb, self.engine, if_exists='append', index = False)
        
        


    def create_websocket(self, coin_usdt_symb, on_open, on_close, on_message, stream_str):
        SOCKET = f"wss://stream.binance.com:9443/ws/{coin_usdt_symb.lower()}{stream_str}"
        return websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message) # add ping pong ?

    def create_df(self, symbol, time, close):
        df_row = {'Symbol':symbol,'Time': time,'Close': close}
        df = pd.DataFrame([df_row])
        df.Close = df.Close.astype(float)
        df.Time = pd.to_datetime(df.Time, unit = 'ms')
        return df

    def get_most_recent_db(self): # returns a dataframe with symbol, time and price
        return pd.read_sql(self.coin_usdt_symb, self.engine)


