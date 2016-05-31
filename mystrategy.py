from datetime import datetime
import matplotlib.pyplot as plt
import logging
import colorlog

from strategy import BaseStrategy

handler = colorlog.StreamHandler()
formatter = colorlog.ColoredFormatter("%(log_color)s%(levelname)s [%(name)s:%(lineno)s] %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class MyStrategy(BaseStrategy):
    type = 'sell'
    balance_store = {}
    price_store = []
    deal_store_sell = []
    deal_store_buy = []

    def start(self):
        self.start_balance = self.balance

    def execute(self, asc, bid, date):
        date = datetime.strptime(date.split('.')[0], '%Y-%m-%dT%H:%M:%S')
        self.price_store.append([date, asc])
        if self.set_order(asc, 1, self.type, stop_loss=10, take_profit=10):
            if self.type == 'buy':
                self.deal_store_buy.append([date, asc])
                self.type = 'sell'
            else:
                self.deal_store_sell.append([date, asc])
                self.type = 'buy'
        if not self.balance_store:
            self.balance_store[date] = self.start_balance
        if not self.orders:
            self.balance_store[date] = self.balance

    def finish(self):
        x = range(len(self.balance_store))
        y = list([self.balance_store[x] for x in self.balance_store])
        plt.plot(x, y)
        plt.axis([x[0], x[-1], 0, max(y)])
        plt.title('Start Balance: {} End Balance: {} Marg: {}'.format(self.start_balance, int(self.balance),
                                                                      int(self.balance-self.start_balance)))
        plt.savefig("Balance.pdf", format='pdf')

        x_total = list([x[0] for x in self.price_store])
        y_total = list([x[1] for x in self.price_store])

        x_deal_sell = list([x[0] for x in self.deal_store_sell])
        y_deal_sell = list([x[1] for x in self.deal_store_sell])

        x_deal_buy = list([x[0] for x in self.deal_store_buy])
        y_deal_buy = list([x[1] for x in self.deal_store_buy])

        plt.plot(x_total, y_total, 'y', x_deal_sell, y_deal_sell, '.r', x_deal_buy, y_deal_buy, '.g')
        plt.axis([x_total[0], x_total[-1], min(y_total), max(y_total)])
        plt.xlabel('time')
        plt.ylabel('Price')
        plt.title('Price')
        b = 0
        for item in self.price_store:
            if item[0] in self.balance_store:
                b += 1
                if b > 30:
                    if self.balance_store[item[0]] > self.start_balance or \
                                    self.balance_store[item[0]] < self.start_balance*0.3:
                        b = 0
                        plt.annotate(
                            int(self.balance_store[item[0]]),
                            xy = (item[0], item[1]),
                            xytext = (-40, 40),
                            textcoords = 'offset points', ha = 'right', va = 'bottom',
                            bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                            arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0')
                        )

        plt.savefig("Price.pdf", format='pdf')

        print('marg', self.balance - self.start_balance)
        print('count', len(self.balance_store))