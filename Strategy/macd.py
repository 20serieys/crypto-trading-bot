import pandas as pd

class macd_strat:
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

    def macd_line(self,df:pd.DataFrame, close_col:str=None, ma_s:int=None, ma_l:int=None, exponential=False):
        if close_col == None:
            close_col = self.close_col
        if ma_s == None:
            ma_s = int(12*24*60/5) # for 5 min intervals
        if ma_l == None:
            ma_l = int(26*24*60/5) # for 5 min intervals
        macd_df = df.copy()
        if 'ma_s' not in macd_df.columns:
            if exponential:
                macd_df = self.exponential_moving_average(macd_df,ma_s,close_col,col_name='ma_s') 
            else:
                macd_df = self.moving_average(macd_df,ma_s,close_col,col_name='ma_s') 
        if 'ma_l' not in macd_df.columns:
            if exponential:
                macd_df = self.exponential_moving_average(macd_df,ma_l,close_col,col_name='ma_l')
            else:
                macd_df = self.moving_average(macd_df, ma_l, close_col,col_name='ma_l')
        macd_df['macd_line'] = macd_df['ma_s'] - macd_df['ma_l']
        return macd_df


    def signal_line(self,df:pd.DataFrame, n_average:int=None, macd_col:str='macd_line', ma_s:int=None, ma_l:int=None, exponential=False): #ma_s and ma_l used only if macd_line not in df index
        if n_average == None:
            n_average = int(9*24*60/5) # for 5 minutes intervals
        if ma_s == None:
            ma_s = int(12*24*60/5) # for 5 min intervals
        if ma_l == None:
            ma_l = int(26*24*60/5) # for 5 min intervals        
        signal_df = df.copy()
        if macd_col not in signal_df.columns:
            signal_df =  self.macd_line(df=signal_df,close_col=self.close_col, ma_s=ma_s,ma_l=ma_l,exponential=exponential)
        if exponential:
            signal_df['signal_line'] = signal_df[macd_col].ewm(span=n_average,min_periods=n_average).mean()
        else:
            signal_df['signal_line'] = signal_df[macd_col].rolling(window=n_average,min_periods=n_average).mean()
        return signal_df

    def strat(self, df, is_buying, is_selling, ma_df = None): #ma_s is the short moving average, ma_l is the long moving average
        if ma_df == None:
            # ma_df = self.macd_line(df=df,close_col=self.close_col,ma_s=self.ma_s,ma_l=self.ma_l,exponential=self.exponential)
            ma_df = self.signal_line(df = df, n_average=self.signal_average, macd_col = 'macd_line',ma_s=self.ma_s,ma_l=self.ma_l, exponential=self.exponential)
        last_macd, last_signal = ma_df['macd_line'].iloc[-1], ma_df['signal_line'].iloc[-1]
        if is_buying:
            if (last_macd < 0)&(last_signal < 0):
                return self.buy_order()
        if is_selling:
            if (last_macd > 0)&(last_signal > 0):
                return self.sell_order()
        return False, False

    def buy_order(self):
        return True,False

    def sell_order(self):
        return False,True

    # def old_strat(self, df, is_buying, is_selling, ma_df = None):
    #     if ma_df == None:
    #         if self.exponential:
    #             ma_df = self.exponential_moving_average(df=df,n_average=self.ma_s,col_name='ma_s')
    #             ma_df = self.exponential_moving_average(df=ma_df,n_average=self.ma_l, col_name='ma_l')
    #         else:
    #             ma_df = self.moving_average(df=df, n_average=self.ma_s, col_name='ma_s')
    #             ma_df = self.moving_average(df=ma_df, n_average=self.ma_l, col_name='ma_l')
    #          #TODO if len(df) < ma1 ou ma1, problemes 
    #     ma_s_col_name = 'ma_s'
    #     ma_l_col_name = 'ma_l'
    #     last_ma_s, last_ma_l = ma_df[ma_s_col_name].iloc[-1], ma_df[ma_l_col_name].iloc[-1]
    #     if is_buying:
    #         if last_ma_s > last_ma_l:
    #             return self.buy_order()
    #     if is_selling:
    #         if last_ma_l > last_ma_s:
    #             return self.sell_order()
    #     return False, False