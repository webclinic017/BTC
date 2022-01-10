from datetime import datetime
import pathlib
import backtrader as bt
# from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader.analyzers as btanalyzers
from reference.Strategy import zwpy_sta
import pandas as pd


BTC_data = pathlib.Path().cwd() / "data" / "training_set.csv"


cerebro = bt.Cerebro()
# cerebro.addstrategy(zwpy_sta.MacdV2Strategy)
cerebro.optstrategy(
            zwpy_sta.MacdV2Strategy,
            fast_period = range(10,14),
            slow_period = range(24,28),
            signal_period = range(8,12))
cerebro.broker.setcash(100000)

dt_start = datetime.strptime("20190925","%Y%m%d")
dt_end = datetime.strptime("20210101","%Y%m%d")
data = bt.feeds.GenericCSVData(
    timeframe = bt.TimeFrame.Minutes,
    compression = 60,
    dataname=BTC_data,
    fromdate=dt_start,      
    todate=dt_end,
    nullvalue=0.0,
    dtformat=('%Y-%m-%d %H:%M:%S'),   
    datetime=0,          
    open = 1,
    high = 2,
    low = 3,
    close = 4,
    openinterest=-1,
    volume = -1
)
# data = bt.feeds.GenericCSVData( dataname=BTC_data, datetime=0, open=1, high=2, low=3, close=4, volume=5, openinterest=-1, dtformat=('%Y-%m-%d %H:%M:%S'), timeframe=bt.TimeFrame.Minutes, compression=60, )
cerebro.adddata(data)
# print('Starting Value: %.2f' % cerebro.broker.getvalue())
cerebro.addanalyzer(btanalyzers.Returns, _name = "returns")
cerebro.addanalyzer(btanalyzers.SharpeRatio, _name = "sharpe")
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
results = cerebro.run()
# print([ele for ele in results])
# print('Ending Value: %.2f' % cerebro.broker.getvalue())
# def run_pyfolio(**kwargs):
par_list = [[ele[0].params.fast_period, 
            ele[0].params.slow_period,
            ele[0].params.signal_period,
            ele[0].analyzers.returns.get_analysis()['rtot'], 
            ele[0].analyzers.sharpe.get_analysis()['sharperatio']
            ] for ele in results]

# Save result to csv
par_df = pd.DataFrame(par_list, columns = ['fast_period', 'slow_period', 'signal_period', 'return', 'sharpe'])
print(par_df.head())
par_df.to_csv('./report/result.csv')
