from pyoanda import Client, TRADE, PRACTICE, Order

from abc import ABCMeta, abstractmethod, abstractproperty
import uuid
from datetime import datetime
import matplotlib.pyplot as plt
import logging
import colorlog

import settings
from backtesting import BackTesting
handler = colorlog.StreamHandler()
formatter = colorlog.ColoredFormatter("%(log_color)s%(levelname)s [%(name)s:%(lineno)s] %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class BaseStrategy(object):
    __metaclass__ = ABCMeta

    def __init__(self, balance, instrument, instruments_list, trade_obj):
        self.trade = trade_obj
        self.orders = {}
        self.balance = float(balance)
        self.instruments_list = instruments_list
        self.pip = 0
        self.maxTradeUnits = 0
        for instruments in self.instruments_list['instruments']:
            if instruments['instrument'] == instrument:
                self.pip = instruments['pip']
                self.maxTradeUnits = instruments['maxTradeUnits']
        if not self.pip:
            raise Exception('Instrument was not found!')

    def tick(self, asc, bid, date):
        pass

    def set_order(self, price, count, type):
        if price <= 0:
            return False
        logger.debug('You try {} instrument (count: {}, price:{})!'.format(type, count, price))
        if type != 'buy' and type != 'sell':
            raise Exception('Unknow type!')
        point_price = self.price_point(price)
        min_balance = point_price*count/self.trade.shoulder
        logger.info('Point price is {}.'.format(point_price))
        if type == 'buy':
            type_invert = 'sell'
        else:
            type_invert = 'buy'

        if type_invert not in self.orders:
            if self.balance < min_balance:
                logger.warning('You not have enough money!')
                return False
            logger.debug('You need {}.'.format(point_price*count))
            if type not in self.orders:
                self.orders[type] = {}
            if self.balance >= point_price*count:
                self.orders[type] = {uuid.uuid4(): {'count': count, 'price': price}}
                self.balance -= point_price*count
                logger.info('You made to {}. Sum is {}. Balance: {}'.format(type, point_price*count, self.balance))
                return {'count': count, 'price': price}
            else:
                logger.warning('You not have enough money!')
        else:
            logger.debug('You have opposite order.')
            for order_key in list(self.orders[type_invert]):
                if self.orders[type_invert][order_key]['count'] == count:
                    del self.orders[type_invert][order_key]
                    self.balance += count+point_price
                    logger.info('You made to {}. Sum is {}. Balance: {}'.format(type, point_price*count, self.balance))
                elif self.orders[type_invert][order_key]['count'] > count:
                    self.orders[type_invert][order_key]['count'] -= count
                    self.balance += count+point_price
                    logger.info('You made to {}. Sum is {}. Balance: {}'.format(type, point_price*count, self.balance))
                elif self.orders[type_invert][order_key]['count'] < count:
                    diff_count = count - self.orders[type_invert][order_key]['count']
                    self.set_order(price, self.orders[type_invert][order_key]['count'], type)
                    self.set_order(price, diff_count, type)

            if not self.orders[type_invert]:
                del self.orders[type_invert]
            return {'count': count, 'price': price}

    def price_point(self, price):
        return (float(self.maxTradeUnits)*float(self.pip)/float(price))/self.trade.shoulder

    @abstractmethod
    def execute(self, asc, bid, date): pass

    @abstractmethod
    def finish(self): pass

    @abstractmethod
    def start(self): pass


class BaseTrade(object):
    def __init__(self):
        self.instrument = 'EUR_USD'
        self.balance = 100
        self.shoulder = 10
        self.client = Client(
            environment=PRACTICE,
            account_id=settings.ACCOUNT,
            access_token=settings.TOKEN
        )
        self.instruments_list = self.get_instruments()

    def get_instruments(self):
        return self.client.get_instruments()

    def back_testing(self, dataframe, strategy, trade_obj):
        BackTesting(dataframe, strategy, self.balance, self.instrument, self.instruments_list, trade_obj)

class MyStrategy(BaseStrategy):
    type = 'buy'
    balance_store = {}
    price_store = []
    deal_store_sell = []
    deal_store_buy = []

    def start(self):
        self.start_balance = self.balance

    def execute(self, asc, bid, date):
        date = datetime.strptime(date.split('.')[0], '%Y-%m-%dT%H:%M:%S')
        self.price_store.append([date, asc])
        if self.set_order(asc, 1, self.type):
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


if __name__ == "__main__":
    trade_obj = BaseTrade()
    dataframe = []
    history_items = trade_obj.client.get_instrument_history(trade_obj.instrument, granularity='S5')
    for item in history_items['candles']:
        dataframe.append({'asc': item['openAsk'],
                          'bid': item['openBid'], 'date': item['time']})
    trade_obj.back_testing(dataframe, MyStrategy, trade_obj)