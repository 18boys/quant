import backtrader as bt


class MyOnly(bt.Sizer):
    params = (('stake', 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            return abs(int(cash / self.p.stake))

        # Sell situation
        position = self.broker.getposition(data)
        if not position.size:
            return 0  # do not sell if nothing is open

        return self.p.stake
