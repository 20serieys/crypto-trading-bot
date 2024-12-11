import pandas as pd

def rsi(df, close_col:str, periods:int): # returns df with column rsi
    diff = df[close_col].diff()
    up = diff.clip(lower=0)
    down = -1 * diff.clip(upper=0)
    up_ewm = up.ewm(com = periods - 1, adjust = True, min_periods=periods).mean()
    down_ewm = down.ewm(com = periods - 1, adjust = True, min_periods=periods).mean()

    rs = up_ewm/down_ewm
    df['rsi'] = 100 - (100/(1+rs))
    return df

def moving_average(df:pd.DataFrame, n_average:int, close_col:str='Price',col_name=None): # returns df with new column
    if col_name == None:
        col_name = f'ma{n_average}'
    ma_df = df.copy()
    ma_df[col_name] = df[close_col].rolling(window=n_average, min_periods=n_average).mean()
    return ma_df

def exponential_moving_average(df:pd.DataFrame, n_average:int, close_col:str='Price',col_name=None):
    if col_name == None:
        col_name = f'ma{n_average}'
    ma_df = df.copy()
    ma_df[col_name] = df[close_col].ewm(span=n_average, min_periods=n_average).mean()
    return ma_df

def macd_line(df:pd.DataFrame, close_col:str='Price', ma_s:int=None, ma_l:int=None, exponential=False):
    if ma_s == None:
        ma_s = int(12*24*60/5) # for 5 min intervals
    if ma_l == None:
        ma_l = int(26*24*60/5) # for 5 min intervals
    macd_df = df.copy()
    if 'ma_s' not in macd_df.columns:
        if exponential:
            macd_df = exponential_moving_average(macd_df,ma_s,close_col,col_name='ma_s') 
        else:
            macd_df = moving_average(macd_df,ma_s,close_col,col_name='ma_s') 
    if 'ma_l' not in macd_df.columns:
        if exponential:
            macd_df = exponential_moving_average(macd_df,ma_l,close_col,col_name='ma_l')
        else:
            macd_df = moving_average(macd_df, ma_l, close_col,col_name='ma_l')
    macd_df['macd_line'] = macd_df['ma_s'] - macd_df['ma_l']
    return macd_df

def signal_line(df:pd.DataFrame, n_average:int=None, macd_col:str='macd_line', ma_s:int=None, ma_l:int=None, exponential=False): #ma_s and ma_l used only if macd_line not in df index
    if n_average == None:
        n_average = int(9*24*60/5) # for 5 minutes intervals
    if ma_s == None:
        ma_s = int(12*24*60/5) # for 5 min intervals
    if ma_l == None:
        ma_l = int(26*24*60/5) # for 5 min intervals        
    signal_df = df.copy()
    if macd_col not in signal_df.columns:
        signal_df =  macd_line(signal_df, n_average, macd_col, ma_s,ma_l,exponential)
    if exponential:
        signal_df['signal_line'] = signal_df[macd_col].ewm(span=n_average,min_periods=n_average).mean()
    else:
        signal_df['signal_line'] = signal_df[macd_col].rolling(window=n_average,min_periods=n_average).mean()
    return signal_df