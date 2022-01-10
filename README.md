# Backtrader

## 環境安裝
pip install -r requirements.txt

pip install git+https://github.com/quantopian/pyfolio.git

## 程式說明

`train_opt.py`
> 使用 Macd 策略進行 Grid search 存取各項評估指標 篩選最佳參數
> 
> Data : BTC_hour.csv
> 
> 回測區間 : 20190925 - 20210101

`default.py`
> 使用 MACDV2 策略進行回測 並輸出風險指標
> 
> Data : BTC_hour.csv
> 
> 回測區間 : 20210101 - 20211028

`buyandhold.py`
> 使用 buyandhold 策略進行回測 存取買賣點與資產淨值時間序列
> 
> Data : BTC_hour.csv
> 
> 回測區間 : 20210101 - 20211028

