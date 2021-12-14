from datetime import datetime
from reference.Strategy.BaseStrategyFrame import BaseStrategyFrame
import pathlib
import backtrader as bt
import pandas as pd
import json

curr_folder = pathlib.Path().cwd()
data_folder = curr_folder / "data"


BTC_test_data = data_folder / "testing_set.csv"

report_timeseries = curr_folder / "report" / "time_series.json"
if not report_timeseries.exists():
    new_timeseries = {
        "train_default":[],
        "train_best":[],
        "test_default":[],
        "test_best":[]
    }
    with open (report_timeseries, "w") as f:
        json.dump(new_timeseries, f, indent = 4) 

with open(report_timeseries) as f:
    time_series = json.load(f)

class MacdV2Strategy(BaseStrategyFrame):
    """
    Implementing the macd20 strategy from zwPython.

    Rule:
        If MACD - MACD_signal > 0: buy.
        If MACD - MACD_signal < 0: sell.

    Args:
        fast_period (int): fast ema period.
        slow_period (int): slow ema period.
        signal_period (int): macd signal period.
    """

    fast_period = 12
    slow_period = 26
    signal_period = 9
    params = (("fast_period", fast_period), ("slow_period", slow_period), ("signal_period", signal_period))
    tmp = []
    def __init__(self):

        # multiple inheritance
        super(MacdV2Strategy, self).__init__()

        print("printlog:", self.params.printlog)
        print("period_me1:", self.params.fast_period)
        print("period_me2:", self.params.slow_period)
        print("period_signal:", self.params.signal_period)

        # Add indicators
        self.macd = bt.indicators.MACD(
            self.dataclose,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period,
        )

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log("Close, %.2f" % self.dataclose[0])
        self.log(
            "O:{:.2f}, H:{:.2f}, L:{:.2f}, C:{:.2f}".format(
                self.dataopen[0], self.datahigh[0], self.datalow[0], self.dataclose[0]
            )
        )
        self.tmp.append(cerebro.broker.getvalue())
        # self.timeseries.train_default.append(pd.Series(cerebro.broker.getvalue()), ignore_index=True)
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.macd.macd[0] > self.macd.signal[0]:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log("BUY CREATE, %.2f" % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:

            if self.macd.macd[0] < self.macd.signal[0]:

                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log("SELL CREATE, %.2f" % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
    
    def stop(self):
        # self.log('Ending Value %.2f' % self.broker.getvalue(), doprint=True)
        print("=== Backtesting Finished! ===")
        time_series['test_default'] = self.tmp
        with open (report_timeseries, "w") as f:
            json.dump(time_series, f, indent = 4) 


cerebro = bt.Cerebro()
cerebro.addstrategy(MacdV2Strategy)
cerebro.broker.setcash(100000)

dt_start = datetime.strptime("20210101","%Y%m%d")
dt_end = datetime.strptime("20210928","%Y%m%d")
data = bt.feeds.GenericCSVData(
    timeframe = bt.TimeFrame.Minutes,
    compression = 60,
    dataname=BTC_test_data,
    fromdate=dt_start,      
    todate=dt_end,
    nullvalue=0.0,
    dtformat=('%Y-%m-%d %H:%M:%S'),   
    datetime=0,             # 各列的位置，从0开始，如列缺失则为None，-1表示自动根据列名判断
    open = 1,
    high = 2,
    low = 3,
    close = 4,
    openinterest=-1,
    volume = -1
)
# data = bt.feeds.GenericCSVData( dataname=BTC_data, datetime=0, open=1, high=2, low=3, close=4, volume=5, openinterest=-1, dtformat=('%Y-%m-%d %H:%M:%S'), timeframe=bt.TimeFrame.Minutes, compression=60, )
cerebro.adddata(data)
print('Starting Value: %.2f' % cerebro.broker.getvalue())
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
results = cerebro.run()
print('Ending Value: %.2f' % cerebro.broker.getvalue())
strat = results[0]
pyfoliozer = strat.analyzers.getbyname('pyfolio')
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
import pyfolio as pf

pf.create_full_tear_sheet(returns,)
# cerebro.plot(iplot = False)