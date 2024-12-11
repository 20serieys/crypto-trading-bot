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
from live_db import live_db
sys.path.append(os.path.abspath("..\Strategy"))
from default_strategy import def_strat
sys.path.append(os.path.abspath("..\Slack"))
from slackapi import SlackMessage

class trading_bot():
    def __init__(self, api_key:str, api_secret:str, coin_symb:str, coin_usdt_symb:str, quantity:float, db_name:str, is_buying:bool=False, is_selling:bool=False, stream_str:str='@kline_1m', periods=20, overbought=70, underbought=30):
        self.client = Client(api_key, api_secret)
        self.portfolio = self.get_portfolio(coin_symb)
        self.balance = self.get_balance()
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_buying = is_buying
        self.is_selling = is_selling
        self.buy_history = []
        self.sell_history = []
        self.balance_history = []
        self.coin_symb = coin_symb # only for balance
        self.coin_usdt_symb = coin_usdt_symb
        self.quantity = quantity
        self.db_name = db_name
        self.stream_str = stream_str
        self.overbought = overbought
        self.underbought = underbought
        self.periods = periods
        self.engine = self.create_engine()
        self.slack_channel_url = "https://hooks.slack.com/services/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"
        self.slack_bot = SlackMessage(webhook_url=self.slack_channel_url)
        # self.ws = self.create_websocket(self.coin_usdt_symb, self.on_open, self.on_close, self.on_message, self.stream_str)
        self.strategy = def_strat(close_col='Close',periods=periods)


    def run_trade(self):
        pass


    def trade(self):
        print(f'pactole de départ: {self.balance}')
        self.slack_bot.send_text_message("z'est bardii")
        while True:
            sleep(2) # better way : check for db update
            df = self.get_recent_db().iloc[-self.periods-2:]
            buy, sell = self.get_decision(df=df,overbought=self.overbought, underbought=self.underbought,is_buying=self.is_buying, is_selling=self.is_selling) # return bools
            if buy:
                # buy_order = self.make_buy_order(quantity=self.quantity) # Just in case there's an error, but doesn't do anything
                print('jachete')
                self.update_buy_history(self.coin_usdt_symb, self.quantity)
                self.update_balance_and_portfolio(brut_qty=self.quantity, sign='+')
                self.update_status(selling=True)
                self.slack_buy_message()
            elif sell:
                # sell_order = self.make_sell_order() # just in case there's an error
                print('bibi')
                self.update_sell_history(self.coin_usdt_symb, self.portfolio) # to simplify, we always sell the whole portfolio
                self.update_balance_and_portfolio(brut_qty=self.portfolio, sign='-') # to simplify, we always sell the whole portfolio
                self.update_status(buying=True)
                self.slack_sell_message()


    def run_live_db(self): 
        ldb = live_db(coin_usdt_symb=self.coin_usdt_symb, db_name=self.db_name, stream_str=self.stream_str)
        ldb.run_ws()


    def get_decision(self,df, overbought, underbought, is_buying, is_selling): # should we buy or sell ?
        return self.strategy.strat(df, overbought, underbought, is_buying, is_selling)

    def get_recent_db(self):
        return pd.read_sql(self.coin_usdt_symb, self.engine)

    def update_buy_history(self,coin:str, qty:float):
        buy_order = {'coin':coin, 'quantity':qty, 'time':datetime.datetime.now()}
        self.buy_history.append(buy_order)
 

    def update_sell_history(self,coin:str, qty:float):
        sell_order = {'coin':coin, 'quantity':qty, 'time':datetime.datetime.now()}
        self.sell_history.append(sell_order)

    def get_portfolio(self, symbol):
        asset_dic = self.client.get_asset_balance(asset=symbol)
        return float(asset_dic['free'])

    def get_balance(self):
        amount = self.client.get_asset_balance(asset='USDT')['free']
        return float(amount)

    def make_buy_order(self, quantity):
        return self.client.create_test_order(symbol=self.coin_usdt_symb, side='BUY', type='MARKET', quantity=quantity, newOrderRespType='RESULT')

    def make_sell_order(self,quantity):
        return self.client.create_test_order(symbol=self.coin_usdt_symb, side='SELL', type='MARKET', quantity=quantity, newOrderRespType='RESULT')

    def update_balance_and_portfolio(self, brut_qty:float, sign:str):
        amount = brut_qty*self.get_price(self.coin_usdt_symb)
        if sign == '+':
            self.balance -= amount
            self.portfolio += brut_qty
        if sign == '-':
            self.balance += amount
            self.portfolio -= brut_qty
        print(f"balance : {self.balance}")
        self.balance_history.append(self.balance)


    def update_status(self, buying=False, selling=False):
        if buying:
            self.is_buying, self.is_selling = True, False
        if selling:
            self.is_buying, self.is_selling = False, True


    def get_price(self, coin:str):
        df = self.get_recent_db()
        return float(df.iloc[-1]['Close'])

    def create_engine(self):
        engine_url = f"sqlite:///..\Dbs\{self.db_name}stream.db"  # to change ?
        engine = sqlalchemy.create_engine(engine_url)
        return engine


# Slack part
    def slack_buy_message(self):
        self.slack_bot.buy_message(self.balance,self.coin_symb)

    def slack_sell_message(self):
        self.slack_bot.sell_message(self.balance,self.coin_symb)