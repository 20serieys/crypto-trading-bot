import sys 
import os
import pandas as pd
from time import sleep
import sqlalchemy
from binance.client import Client
import datetime
import websocket
import json

sys.path.append(os.path.abspath("..\Database"))
from backtest_db import backtesting_db
sys.path.append(os.path.abspath("..\Strategy"))
from default_strategy import def_strat
from macd import macd_strat
from ma import ma_strat
sys.path.append(os.path.abspath("..\Slack"))
from slackapi import SlackMessage


# time interval is db_time_interval but as an int / periods is for rsi / ma_s and ma_l in days, converted using time_interval
class trading_bot():
    def __init__(self, api_key:str, api_secret:str, coin_symb:str, coin_usdt_symb:str, quantity:float, start_date:str, end_date:str, db_time_interval:int, time_interval, is_buying:bool=False, is_selling:bool=False, strategy = 'default', periods=20, overbought=70, underbought=30, ma_s = 12, ma_l= 26, signal_average=9, fees = 0.001):
        self.client = Client(api_key, api_secret)
        self.portfolio = 0
        self.balance = 15
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_buying = is_buying
        self.is_selling = is_selling
        self.start_date = start_date
        self.end_date = end_date
        self.buy_history = []
        self.sell_history = []
        self.balance_history = [self.balance]
        self.coin_symb = coin_symb # only for balance
        self.coin_usdt_symb = coin_usdt_symb
        self.quantity = quantity
        self.periods = periods
        self.overbought = overbought
        self.underbought = underbought
        self.ma_s = ma_s
        self.ma_l = ma_l
        self.signal_average = signal_average
        self.fees = fees
        # self.ws = self.create_websocket(self.coin_usdt_symb, self.on_open, self.on_close, self.on_message, self.stream_str)
        if strategy == 'default':
            self.strategy = def_strat(close_col='Price',periods=periods, underbought=underbought, overbought=overbought)
        elif strategy == 'macd':
            self.strategy = macd_strat(close_col='Price',ma_s=self.ma_s, ma_l=self.ma_l, signal_average=self.signal_average, exponential=False) # exponential can be changed
        elif strategy == 'ma':
            self.strategy = ma_strat(close_col='Price',ma_s=self.ma_s, ma_l=self.ma_l, signal_average=self.signal_average, exponential=True)
        else:
            raise Exception('unknown strategy')
        self.db_time_interval = db_time_interval
        self.time_interval = time_interval
        self.db = self.get_db()
        self.trade_number = 0


    def trade(self):
        print(f'pactole de départ: {self.balance}')
        backtesting_db_length = self.ma_l
        for time in range(backtesting_db_length+5,len(self.db)): #TODO début du range hardcodé pas ouf 
            df = self.db.iloc[time-backtesting_db_length-2:time].copy() # pareil changer à la main quand on change de strat
            if self.is_buying:
                buy, sell = self.get_decision(df=df,is_buying=self.is_buying, is_selling=self.is_selling) # return bools
                if buy:
                    self.update_buy_history(coin=self.coin_usdt_symb, qty=self.quantity,price=self.get_price(time), time=time)
                    self.update_balance_and_portfolio(brut_qty=self.quantity, sign='+', time=time)
                    self.update_status(selling=True)
            elif self.is_selling:
                if self.stop_loss(time):
                    self.update_sell_history(coin=self.coin_usdt_symb, qty=self.portfolio, price=self.get_price(time), time=time) # to simplify, we always sell the whole portfolio
                    self.update_balance_and_portfolio(brut_qty=self.portfolio, sign='-', time=time) # to simplify, we always sell the whole portfolio
                    self.update_status(buying=True)
                    continue # test
                buy, sell = self.get_decision(df=df,is_buying=self.is_buying, is_selling=self.is_selling) # return bools
                if sell:
                    self.update_sell_history(coin=self.coin_usdt_symb, qty=self.portfolio, price=self.get_price(time), time=time) # to simplify, we always sell the whole portfolio
                    self.update_balance_and_portfolio(brut_qty=self.portfolio, sign='-', time=time) # to simplify, we always sell the whole portfolio
                    self.update_status(buying=True)
        return max(self.balance_history[-2], self.balance_history[-1])

    def get_db(self):
        bdb = backtesting_db(api_key=self.api_key, api_secret=self.api_secret, coin_usdt_symb = self.coin_usdt_symb, db_time_interval = self.db_time_interval, start_date=self.start_date, end_date=self.end_date)
        return bdb.get_data()


    def get_decision(self, df, is_buying, is_selling): # should we buy or sell ?
        return self.strategy.strat(df, is_buying, is_selling)

    def stop_loss(self,time):
        buying_price = self.buy_history[-1]['price']
        current_price = self.get_price(time)
        if current_price < 0.95*buying_price:
            print(f'stop loss, current price = {current_price}')
            return True
        return False

    def update_buy_history(self,coin:str, qty:float, price:float, time:int):
        buy_order = {'coin':coin, 'quantity':qty, 'price':price, 'time':time}
        self.buy_history.append(buy_order)
 

    def update_sell_history(self,coin:str, qty:float, price:float, time:int):
        sell_order = {'coin':coin, 'quantity':qty, 'price':price, 'time':time}
        self.sell_history.append(sell_order)

    def make_buy_order(self, quantity):
        pass 

    def make_sell_order(self,quantity):
        pass

    def update_balance_and_portfolio(self, brut_qty:float, sign:str, time:int):
        amount = brut_qty*self.get_price(time)
        if sign == '+':
            self.balance -= amount*(1+ self.fees) # accounting for fees
            self.portfolio += brut_qty
        if sign == '-':
            self.balance += amount*(1 - self.fees) # accounting for fees
            self.portfolio -= brut_qty
            self.trade_number +=1
            date = self.db.iloc[time]['Time'].strftime('%Y-%m-%d %T')
            print(f"balance : {self.balance}, trade_number :{self.trade_number}, date :{date}, price :{self.get_price(time)}")
        self.balance_history.append(self.balance)


    def update_status(self, buying=False, selling=False):
        if buying:
            self.is_buying, self.is_selling = True, False
        if selling:
            self.is_buying, self.is_selling = False, True


    def get_price(self, time:int):
        return float(self.db.iloc[time]['Price'])
