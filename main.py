from pyoanda import Client, TRADE, PRACTICE, Order

import settings
from backtesting import BackTesting
from mystrategy import MyStrategy


class BaseTrade(object):
    def __init__(self):
        self.instrument = 'EUR_USD'
        self.balance = 100
        self.shoulder = 100
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

if __name__ == "__main__":
    trade_obj = BaseTrade()
    dataframe = []
    history_items = trade_obj.client.get_instrument_history(trade_obj.instrument, granularity='S5')
    for item in history_items['candles']:
        dataframe.append({'asc': item['openAsk'],
                          'bid': item['openBid'], 'date': item['time']})
    trade_obj.back_testing(dataframe, MyStrategy, trade_obj)