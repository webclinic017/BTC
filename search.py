from datetime import datetime
import pathlib
import backtrader as bt
import json
# from __future__ import (absolute_import, division, print_function, unicode_literals)

BTC_data = pathlib.Path().cwd() / "BTC_hour.csv"
params_config = pathlib.Path().cwd() / "params.json"
dt_start = datetime.strptime("20190925","%Y%m%d")
dt_end = datetime.strptime("20211028","%Y%m%d")
best_params = dict()
best_params["ending_value"] = 0


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
            cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
            results = cerebro.run()
            print('Ending Value: %.2f' % cerebro.broker.getvalue())
            if cerebro.broker.getvalue() > best_params["ending_value"]:
                best_params["fast_period"] = fast_period
                best_params["slow_period"] = slow_period
                best_params["signal_period"] = signal_period
                best_params["ending_value"] = cerebro.broker.getvalue()
            print(best_params)
# print(f"The Best Paeameters  fast_period:{best_params["fast_period"]}, slow_period{best_params["slow_period"]}, signal_period{best_params["signal_period"]}")
print(f"The Best Parameters : {best_params}")
with open("params.json", "w") as f:
    json.dump(best_params, f, indent = 4) 
                
