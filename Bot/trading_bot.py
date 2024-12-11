import sys 
import os
import asyncio
import pandas as pd
from time import sleep
import sqlalchemy
from binance.client import Client
import datetime

sys.path.append(os.path.abspath("..\Database"))
from live_db import live_db
sys.path.append(os.path.abspath("..\Strategy"))
from default_strategy import def_strat

class trading_bot:
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
        self.coin_symb = coin_symb # only for balance
        self.coin_usdt_symb = coin_usdt_symb
        self.quantity = quantity # qty in usdt we're buying 
        self.db_name = db_name
        self.stream_str = stream_str
        self.overbought = overbought
        self.underbought = underbought
        self.engine = self.create_engine()
        self.strategy = def_strat(close_col='Close',periods=periods)


    async def trade(self):
        await self.run_live_db() # check if works
        while True:
            sleep(2) # better way : check for db update
            df = self.get_recent_db()
            buy, sell = self.get_decision(df=df, overbought=self.overbought, underbought=self.underbought) # FILL return bools
            if buy:
                buy_order = self.make_buy_order(quantity=self.quantity) # should return info about the buy
                self.update_buy_history(buy_order=buy_order)
                self.update_balance()
                self.update_portfolio(self.coin_symb)
                self.update_status(selling=True)
            elif sell:
                sell_order = self.make_sell_order() # should return info about the sell
                self.update_sell_history(sell_order=sell_order)
                self.update_balance()
                self.update_portfolio(self.coin_symb)
                self.update_status(buying=True)


    async def run_live_db(self): # needs to be async
        ldb = live_db(self.api_key, self.api_secret, coin_usdt_symb=self.coin_usdt_symb, db_name=self.db_name, stream_str=self.stream_str)
        ldb.run_ws()


    def get_decision(self,df, overbought, underbought, is_buying, is_selling): # should we buy or sell ?
        return self.strategy.strat(df, overbought, underbought, is_buying, is_selling)

    def get_recent_db(self):
        return pd.read_sql(self.coin_symb_usdt, self.engine)

    def update_buy_history(self,buy_order):
        buy_order['transactTime'] = datetime.datetime.fromtimestamp(buy_order['transactTime']/1000).strftime("%Y-%m-%d %H:%M:%S")
        pop_list = ['clientOrderId','cummulativeQuoteQty','timeInForce','type']
        for poper in pop_list:
            buy_order = buy_order.pop(poper)
        self.buy_history.append(buy_order)
 

    def update_sell_history(self, sell_order):
        sell_order['transactTime'] = datetime.datetime.fromtimestamp(sell_order['transactTime']/1000).strftime("%Y-%m-%d %H:%M:%S")
        pop_list = ['clientOrderId','cummulativeQuoteQty','timeInForce','type']
        for poper in pop_list:
            sell_order = sell_order.pop(poper)
        self.sell_history.append(sell_order)

    def get_portfolio(self, symbol):
        asset_dic = self.client.get_asset_balance(asset=symbol)
        return float(asset_dic['free'])

    def get_balance(self):
        amount = self.client.get_asset_balance(asset='USDT')['free']
        return float(amount)

    def make_buy_order(self, quantity): # quantity is in usdt, it needs to be converted
        coin_qty = quantity/self.get_price(self.coin_usdt_symb)
        return self.client.create_order(symbol=self.coin_usdt_symb, side='BUY', type='MARKET', quantity=coin_qty, newOrderRespType='RESULT')

    def make_sell_order(self,quantity=None): # if quantity is unspecified, sell everythang 
        if quantity == None:
            coin_qty = self.portfolio
        else:
            coin_qty = quantity/self.get_price(self.coin_usdt_symb)

        return self.client.create_order(symbol=self.coin_usdt_symb, side='SELL', type='MARKET', quantity=coin_qty, newOrderRespType='RESULT')

    def update_balance(self):
        amount = self.client.get_asset_balance(asset='USDT')['free']
        self.balance = float(amount)

    def update_portfolio(self, symbol):
        asset_dic = self.client.get_asset_balance(asset=symbol)
        self.portfolio = float(asset_dic['free'])

    def update_status(self, buying=False, selling=False):
        if buying:
            self.is_buying, self.is_selling = True, False
        if selling:
            self.is_buying, self.is_selling = False, True

    def create_engine(self):
        engine_url = f"sqlite:///{self.db_name}stream.db"
        engine = sqlalchemy.create_engine(engine_url)
        return engine

    def get_price(self, coin:str):
        df = self.get_recent_db()
        return df.iloc[-1]['close']



