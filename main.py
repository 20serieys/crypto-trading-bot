import sys 
import os
import pandas as pd
from time import sleep
from binance.client import Client
import datetime
import websocket
import json
from matplotlib import pyplot as plt
sys.path.append(os.path.abspath(".."))
import secret
api_key = secret.api_key
api_secret = secret.api_secret

sys.path.append(os.path.abspath("..\Database"))
sys.path.append(os.path.abspath("..\Bot"))

from backtest_bot import trading_bot

client = Client(api_key, api_secret)

coin_usdt_symb = 'BTCUSDT'
coin_symb='BTC'
quantity=0.001
overbought = 70
underbought = 30
# ma_s = 2*int(24*60/5)
ma_s = 12*12*24
ma_l = 23*12*24
signal_average = 4*12*24
periods = 10
db_time_interval = Client.KLINE_INTERVAL_5MINUTE
time_interval = 5
start_date = "01 Mar, 2022"
end_date = "06 Jun, 2023"
strategy = 'ma'

bt_bot = trading_bot(api_key=api_key, api_secret=api_secret, coin_symb=coin_symb, coin_usdt_symb=coin_usdt_symb, quantity=quantity, start_date=start_date, end_date=end_date, db_time_interval=db_time_interval, time_interval=time_interval, is_buying=True, is_selling=False, periods=periods, overbought=overbought, underbought=underbought, ma_s=ma_s, ma_l=ma_l, signal_average=signal_average, strategy = strategy)

# strat view
# db = bt_bot.db
# db = bt_bot.strategy.exponential_moving_average(df=db,n_average=ma_s,col_name='ma_s')
# db = bt_bot.strategy.exponential_moving_average(df=db,n_average=ma_l,col_name='ma_l')
# db.plot(x='Time',y=['ma_s','ma_l','Price'])

last_high = bt_bot.trade()
print(last_high)