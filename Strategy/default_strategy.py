import pandas as pd

class def_strat:
    def __init__(self, close_col:str, periods:str, underbought:int=30, overbought:str=70):
        self.close_col = close_col
        self.periods = periods
        self.underbought = underbought
        self.overbought = overbought

    def rsi(self, df, close_col:str, periods:int): # returns df with column rsi
        diff = df[close_col].diff()
        up = diff.clip(lower=0)
        down = -1 * diff.clip(upper=0)
        up_ewm = up.ewm(com = periods - 1, adjust = True, min_periods=periods).mean()
        down_ewm = down.ewm(com = periods - 1, adjust = True, min_periods=periods).mean()

        rs = up_ewm/down_ewm
        df['rsi'] = 100 - (100/(1+rs))
        return df

    def strat(self, df, is_buying, is_selling, rsi_df = None):
        if rsi_df == None:
            rsi_df = self.rsi(df, self.close_col, self.periods)
             #TODO if len(rsi_df) < period, problemes 
        rsi_1, rsi_2 = rsi_df.iloc[-2].rsi, rsi_df.iloc[-1].rsi
        if is_buying:
            if(rsi_1 > self.underbought)&(rsi_2 < self.underbought):
                return self.buy_order()
        if is_selling:
            if(rsi_1 < self.overbought)&(rsi_2 > self.overbought):
                return self.sell_order()
        return False, False

    def buy_order(self):
        return True,False

    def sell_order(self):
        return False,True
