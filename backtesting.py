class BackTesting(object):
    def __init__(self, dataframe, class_strategy, balance, instrument, instruments_list, trade_obj):
        if dataframe:
            if 'asc' not in dataframe[0]:
                raise Exception('Option asc was not found in dataframe')
            if 'bid' not in dataframe[0]:
                raise Exception('Option bid was not found in dataframe')
            if 'date' not in dataframe[0]:
                raise Exception('Option date was not found in dataframe')
            object_strategy = class_strategy(balance, instrument, instruments_list, trade_obj)
            if hasattr(object_strategy, 'execute'):
                start = getattr(object_strategy, 'start')
                start()
                method_tick = getattr(object_strategy, 'tick')
                method_strategy = getattr(object_strategy, 'execute')
                for data in dataframe:
                    method_tick(data['asc'], data['bid'], data['date'])
                    method_strategy(data['asc'], data['bid'], data['date'])
                getattr(object_strategy, 'finish')()
            else:
                raise Exception('Method execute was not found')
        else:
            raise Exception('Dataframe is empty!')