from datetime import datetime
from reference.Strategy import zwpy_sta
import pathlib
import backtrader as bt
# from __future__ import (absolute_import, division, print_function, unicode_literals)


BTC_data = pathlib.Path().cwd() / "BTC_hour.csv"


cerebro = bt.Cerebro()
cerebro.addstrategy(zwpy_sta.MacdV2Strategy)
cerebro.broker.setcash(100000)

dt_start = datetime.strptime("20190925","%Y%m%d")
dt_end = datetime.strptime("20211028","%Y%m%d")
data = bt.feeds.GenericCSVData(
    timeframe = bt.TimeFrame.Minutes,
    compression = 60,
    dataname=BTC_data,
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
cerebro.plot(iplot = False)