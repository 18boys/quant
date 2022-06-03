from datetime import datetime

import backtrader as bt  # 升级到最新版
import matplotlib.pyplot as plt  # 由于 Backtrader 的问题，此处要求 pip install matplotlib==3.2.2
import akshare as ak  # 升级到最新版
import pandas as pd

from utils.process import process_data

"""
比特币量化交易策略：
btc ma策略
"""
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

btc_path = 'data/btc.csv'
eth_path = 'data/eth.csv'

# # 首先处理数据格式
# beforData = pd.read_csv(btc_path)

# crypto_hist_df = ak.crypto_hist(symbol="BTC", period="每日", start_date="20151020", end_date="20201023")
# stock_hfq_df = ak.crypto_hist(symbol="BTC", period="每日", start_date="20151020", end_date="20201023")
# 利用 AKShare 获取股票的后复权数据，
stock_hfq_df = process_data(btc_path).iloc[:, :6]  # 这里只获取前 6 列,否则下面x轴只有6个元素将会报错
print(stock_hfq_df.iloc[-2:])
# print(stock_hfq_df.columns)
# exit()

# 处理字段命名，以符合 Backtrader 的要求
stock_hfq_df.columns = [
    'date',
    'close',
    'open',
    'high',
    'low',
    'volume',
]
print(stock_hfq_df.iloc[0:2])
# exit()

# 把 date 作为日期索引，以符合 Backtrader 的要求
stock_hfq_df.index = pd.to_datetime(stock_hfq_df['date'])


class MyStrategy(bt.Strategy):
    """
    主策略程序
    """
    params = (("maperiod", 20),
              ('printlog', False),)  # 全局设定交易策略的参数, maperiod是 MA 均值的长度

    def __init__(self):
        """
        初始化函数
        """
        self.data_close = self.datas[0].close  # 指定价格序列
        # 初始化交易指令、买卖价格和手续费
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        # 添加移动均线指标
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod
        )

    def next(self):
        """
        主逻辑
        """

        # self.log(f'收盘价, {data_close[0]}')  # 记录收盘价
        if self.order:  # 检查是否有指令等待执行,
            return
        # 检查是否持仓
        if not self.position:  # 没有持仓
            # 执行买入条件判断：收盘价格上涨突破15日均线
            if self.data_close[0] > self.sma[0]:
                self.log("BUY CREATE, %.2f" % self.data_close[0])
                # 执行买入
                self.order = self.buy()
        else:
            # 执行卖出条件判断：收盘价格跌破15日均线
            if self.data_close[0] < self.sma[0]:
                self.log("SELL CREATE, %.2f" % self.data_close[0])
                # 执行卖出
                self.order = self.sell()

    def log(self, txt, dt=None, do_print=False):
        """
        Logging function fot this strategy
        """
        if self.params.printlog or do_print:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        """
        记录交易执行情况
        """
        # 如果 order 为 submitted/accepted,返回空
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 如果order为buy/sell executed,报告价格结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"买入:\n价格:{order.executed.price},\
                成本:{order.executed.value},\
                手续费:{order.executed.comm}"
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(
                    f"卖出:\n价格：{order.executed.price},\
                成本: {order.executed.value},\
                手续费{order.executed.comm}"
                )
            self.bar_executed = len(self)

            # 如果指令取消/交易失败, 报告结果
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"交易失败 {order.status}")
        self.order = None

    def notify_trade(self, trade):
        """
        记录交易收益情况
        """
        if not trade.isclosed:
            return
        self.log(f"策略收益：\n毛收益 {trade.pnl:.2f}, 净收益 {trade.pnlcomm:.2f}")

    def stop(self):
        """
        回测结束后输出结果
        """
        self.log("(MA均线： %2d日) 期末总资金 %.2f" % (self.params.maperiod, self.broker.getvalue()), do_print=True)


cerebro = bt.Cerebro()  # 初始化回测系统
start_date = datetime(2018, 1, 1)  # 回测开始时间
end_date = datetime(2022, 1, 1)  # 回测结束时间
data = bt.feeds.PandasData(dataname=stock_hfq_df, fromdate=start_date, todate=end_date)  # 加载数据
cerebro.adddata(data)  # 将数据传入回测系统
# cerebro.addstrategy(MyStrategy)  # 将交易策略加载到回测系统中
cerebro.optstrategy(MyStrategy, maperiod=range(10, 130, 10))  # 导入策略参数寻优

start_cash = 1000000
cerebro.broker.set_coc(True)  # broker设置以当天收盘价交易
cerebro.broker.setcash(start_cash)  # 设置初始资本为 100000
cerebro.broker.setcommission(commission=0.001)  # 设置交易手续费为 0.1%
cerebro.addsizer(bt.sizers.PercentSizerInt, percents=98)  # 设置买入数量 全部进入
cerebro.run(maxcpus=1)  # 用单核 CPU 做优化

port_value = cerebro.broker.getvalue()  # 获取回测结束后的总资金
pnl = port_value - start_cash  # 盈亏统计

print(f"初始资金: {start_cash}\n回测期间：{start_date.strftime('%Y%m%d')}:{end_date.strftime('%Y%m%d')}")
print(f"总资金: {round(port_value, 2)}")
print(f"净收益: {round(pnl, 2)}")

# cerebro.plot(style='candlestick')  # 画图
