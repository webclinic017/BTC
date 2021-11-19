from datetime import datetime
from reference.Strategy import BaseStrategyFrame
from reference.Strategy import zwpy_sta
import pathlib
import backtrader as bt


BTC_data = pathlib.Path().cwd() / "BTC_hour.csv"


cerebro = bt.Cerebro()
cerebro.addstrategy(zwpy_sta.MacdV2Strategy)

# data0 = bt.feeds.YahooFinanceData(dataname=BTC_data, fromdate=datetime(2019, 9, 25),
#                                     todate=datetime(2019, 10, 25))
# cerebro.adddata(data0)
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
cerebro.adddata(data)
print('Starting Value: %.2f' % cerebro.broker.getvalue())
cerebro.run()
print('Ending Value: %.2f' % cerebro.broker.getvalue())
cerebro.plot()
