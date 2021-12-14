from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from datetime import datetime
import pathlib
import backtrader as bt
import json
import pandas as pd

# route init
curr_folder = pathlib.Path().cwd()
BTC_data_min = curr_folder / "data" / "BTCUSDT_UPERP_1m.csv"

# report folder init
report_folder = curr_folder / "report"
if not report_folder.exists():
    report_folder.mkdir(parents=True, exist_ok=True)

BTC_data_min = pd.read_csv(BTC_data_min, parse_dates =["datetime"], index_col ="datetime")
BTC_data = BTC_data_min.resample('h').mean()
data_folder = curr_folder / "data"
if not data_folder.exists():
    data_folder.mkdir(parents=True, exist_ok=True)


params = {
    "train":{
        "default":{
            "fast_period":0,
            "slow_period":0,
            "signal_period":0,
            "starting_value":100000,
            "ending_value":0,
            "profit":0
    },
        "best":{
            "fast_period":0,
            "slow_period":0,
            "signal_period":0,
            "starting_value":100000,
            "ending_value":0,
            "profit":0
    }
    },
    "test":{
        "default":{
            "fast_period":0,
            "slow_period":0,
            "signal_period":0,
            "starting_value":100000,
            "ending_value":0,
            "profit":0
        },
        "best":{
            "fast_period":0,
            "slow_period":0,
            "signal_period":0,
            "starting_value":100000,
            "ending_value":0,
            "profit":0
    }
    }
}

# Cutting dataset
train = BTC_data[BTC_data.index < '2021-01-01 0:00:00']
test = BTC_data[BTC_data.index >= '2021-01-01 0:00:00']
BTC_data.to_csv(str(data_folder / "BTC_hour.csv"))
train.to_csv(str(data_folder / "training_set.csv"))
test.to_csv(str(data_folder / "testing_set.csv"))

BTC_train_data = data_folder / "training_set.csv"
BTC_test_data = data_folder / "testing_set.csv"


dt_start = datetime.strptime("2019-09-25","%Y-%m-%d")
dt_end = datetime.strptime("2020-12-31","%Y-%m-%d")

class BaseStrategyFrame(bt.Strategy):
    """
    Define base Strategy class (main structure),
    so the class structure could remain consistent.

    All Strategy inherit this class.

    Args:
        doprint (int): Whather to print message.
    """

    params = (("printlog", False),)

    def log(self, txt, dt=None, doprint=False):
        """Logging function fot this strategy"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "BUY EXECUTED, Price: %.2f, Size: %.2f, Cost: %.2f, Comm %.2f, Cash %.2f"
                    % (
                        order.executed.price,
                        order.executed.size,
                        order.executed.value,
                        order.executed.comm,
                        self.broker.getcash(),
                    )
                )

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log(
                    "SELL EXECUTED, Price: %.2f, Size: %.2f, Cost: %.2f, Comm %.2f, Cash %.2f"
                    % (
                        order.executed.price,
                        order.executed.size,
                        order.executed.value,
                        order.executed.comm,
                        self.broker.getcash(),
                    )
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    def start(self):
        # self.log('Ending Value %.2f' % self.broker.getvalue(), doprint=True)
        print("=== Backtesting Start! ===")

    def stop(self):
        # self.log('Ending Value %.2f' % self.broker.getvalue(), doprint=True)
        print("=== Backtesting Finished! ===")

# train params
for fast_period in range(11,14):
    for slow_period in range(25,28):
        for signal_period in range(7,11):
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
                params = (("fast_period", fast_period), ("slow_period", slow_period), ("signal_period", signal_period))

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

            cerebro = bt.Cerebro()
            cerebro.addstrategy(MacdV2Strategy)
            cerebro.broker.setcash(100000)
            data = bt.feeds.GenericCSVData(
                timeframe = bt.TimeFrame.Minutes,
                compression = 60,
                dataname=BTC_train_data,
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
            cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
            results = cerebro.run()
            print('Ending Value: %.2f' % cerebro.broker.getvalue())
            if fast_period == 12 and slow_period == 26 and signal_period == 9:
                params["train"]["default"]["fast_period"] = fast_period
                params["train"]["default"]["slow_period"] = slow_period
                params["train"]["default"]["signal_period"] = signal_period
                params["train"]["default"]["ending_value"] = cerebro.broker.getvalue()
                params["train"]["default"]["profit"] = cerebro.broker.getvalue() - 100000


            if cerebro.broker.getvalue() > params["train"]["best"]["ending_value"]:
                params["train"]["best"]["fast_period"] = fast_period
                params["train"]["best"]["slow_period"] = slow_period
                params["train"]["best"]["signal_period"] = signal_period
                params["train"]["best"]["ending_value"] = cerebro.broker.getvalue()
                params["train"]["best"]["profit"] = cerebro.broker.getvalue() - 100000

# test data
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
    params = (("fast_period", params["train"]["best"]["fast_period"]), ("slow_period", params["train"]["best"]["slow_period"]), ("signal_period", params["train"]["best"]["signal_period"]))

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
cerebro = bt.Cerebro()
cerebro.addstrategy(MacdV2Strategy)
cerebro.broker.setcash(100000)
dt_start = datetime.strptime("2020-01-01","%Y-%m-%d")
dt_end = datetime.strptime("2021-10-28","%Y-%m-%d")
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
cerebro.adddata(data)
print('Starting Value: %.2f' % cerebro.broker.getvalue())
results = cerebro.run()
print('Ending Value: %.2f' % cerebro.broker.getvalue())
params["test"]["best"]["fast_period"] = params["train"]["best"]["fast_period"]
params["test"]["best"]["slow_period"] = params["train"]["best"]["slow_period"]
params["test"]["best"]["signal_period"] = params["train"]["best"]["signal_period"]
params["test"]["best"]["ending_value"] = cerebro.broker.getvalue()
params["test"]["best"]["profit"] = cerebro.broker.getvalue() - 100000

# test data default
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
    params = (("fast_period", 12), ("slow_period", 26), ("signal_period", 9))

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
cerebro = bt.Cerebro()
cerebro.addstrategy(MacdV2Strategy)
cerebro.broker.setcash(100000)
dt_start = datetime.strptime("2020-01-01","%Y-%m-%d")
dt_end = datetime.strptime("2021-10-28","%Y-%m-%d")
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
cerebro.adddata(data)
print('Starting Value: %.2f' % cerebro.broker.getvalue())
results = cerebro.run()
print('Ending Value: %.2f' % cerebro.broker.getvalue())
params["test"]["default"]["fast_period"] = 12
params["test"]["default"]["slow_period"] = 26
params["test"]["default"]["signal_period"] = 9
params["test"]["default"]["ending_value"] = cerebro.broker.getvalue()
params["test"]["default"]["profit"] = cerebro.broker.getvalue() - 100000

with open(str(report_folder / "params.json"), "w") as f:
    json.dump(params, f, indent = 4) 