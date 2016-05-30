from abc import ABCMeta, abstractmethod, abstractproperty
import uuid
import logging
import colorlog

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