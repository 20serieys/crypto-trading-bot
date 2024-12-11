import pandas as pd

class ma_strat:
    def __init__(self, close_col:str, ma_s, ma_l, signal_average, exponential = False):
        self.close_col = close_col
        self.ma_s = ma_s
        self.ma_l = ma_l
        self.signal_average = signal_average
        self.exponential = exponential

    def moving_average(self, df:pd.DataFrame, n_average:int, close_col:str = None, col_name=None): # returns df with new column
        if close_col == None:
            close_col = self.close_col
        if col_name == None:
            col_name = f'ma{n_average}'
        ma_df = df.copy()
        ma_df[col_name] = ma_df[close_col].rolling(window=n_average, min_periods=n_average).mean()
        return ma_df

    def exponential_moving_average(self, df:pd.DataFrame, n_average:int, close_col:str=None, col_name=None):
        if close_col == None:
            close_col = self.close_col
        if col_name == None:
            col_name = f'ma{n_average}'        
        ma_df = df.copy()
        ma_df[col_name] = ma_df[close_col].ewm(span=n_average, min_periods=n_average).mean()
        return ma_df

    def buy_order(self):
        return True,False

    def sell_order(self):
        return False,True

    def strat(self, df, is_buying, is_selling, ma_df = None):
        if ma_df == None:
            if self.exponential:
                ma_df = self.exponential_moving_average(df=df,n_average=self.ma_s,col_name='ma_s')
                ma_df = self.exponential_moving_average(df=ma_df,n_average=self.ma_l, col_name='ma_l')
            else:
                ma_df = self.moving_average(df=df, n_average=self.ma_s, col_name='ma_s')
                ma_df = self.moving_average(df=ma_df, n_average=self.ma_l, col_name='ma_l')
             #TODO if len(df) < ma1 ou ma1, problemes 
        ma_s_col_name = 'ma_s'
        ma_l_col_name = 'ma_l'
        last_ma_s, last_ma_l = ma_df[ma_s_col_name].iloc[-1], ma_df[ma_l_col_name].iloc[-1]
        if is_buying:
            if last_ma_s > last_ma_l:
                return self.buy_order()
        if is_selling:
            if last_ma_l > last_ma_s:
                return self.sell_order()
        return False, False