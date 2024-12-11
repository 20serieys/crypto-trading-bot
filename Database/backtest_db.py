import pandas as pd
from binance.client import Client
import sqlalchemy
import datetime as dt
#ref https://python.plainenglish.io/how-to-download-trading-data-from-binance-with-python-21634af30195

class backtesting_db:
    def __init__(self, api_key:str, api_secret:str, coin_usdt_symb:str, db_time_interval:str, start_date:str, end_date:str): # check format of time_interval (possibly Client.KLINE_INTERVAL_15MINUTE with Client imported from binance.client)
        self.coin_usdt_symb = coin_usdt_symb
        self.client = Client(api_key, api_secret)
        self.db_interval = db_time_interval
        self.start_date = start_date
        self.end_date = end_date

    def get_data(self, start_date:str=None, end_date:str=None): # returns a df. check if it matches the format of live_db df. Pass dates as arguments
        if start_date == None:
            start_date = self.start_date
        if end_date == None:
            end_date = self.end_date
        klines = self.client.get_historical_klines(self.coin_usdt_symb, self.db_interval, start_str=start_date, end_str=end_date)
        df = pd.DataFrame(klines)
        df.columns = ['open_time','open', 'high', 'low', 'Price', 'volume','close_time', 'qav','num_trades','taker_base_vol','taker_quote_vol', 'ignore']
        df['Time'] = [dt.datetime.fromtimestamp(time/1000.0) for time in df.close_time]
        df.Price = df.Price.astype(float)
        # add coin_usdt_symb column and select only the columns needed to match live_db df format
        df['Symbol'] = self.coin_usdt_symb
        df = df.loc[:,['Symbol', 'Time', 'Price']]
        return df

    def write_db(self, df, db_name = None):
        if db_name == None:
            # convert date format
            start_date = dt.datetime.strptime(self.start_date, '%d %b, %Y').strftime('%Y-%m-%d')
            end_date = dt.datetime.strptime(self.end_date, '%d %b, %Y').strftime('%Y-%m-%d')
            db_name = f'{self.coin_usdt_symb}_{start_date}_{end_date}_{self.interval}'
        engine_url = f"sqlite:///..\Dbs\{db_name}.db"
        engine = sqlalchemy.create_engine(engine_url)
        df.to_sql(self.coin_usdt_symb, engine, if_exists='replace', index = False) # tester

    def read_db(self, db_name = None):
        if db_name == None:
            start_date = dt.datetime.strptime(self.start_date, '%d %b, %Y').strftime('%Y-%m-%d')
            end_date = dt.datetime.strptime(self.end_date, '%d %b, %Y').strftime('%Y-%m-%d')
            db_name = f'{self.coin_usdt_symb}_{start_date}_{end_date}_{self.interval}'
        engine_url = f"sqlite:///..\Dbs\{db_name}.db"
        engine = sqlalchemy.create_engine(engine_url)
        return pd.read_sql(self.coin_usdt_symb, engine)




        