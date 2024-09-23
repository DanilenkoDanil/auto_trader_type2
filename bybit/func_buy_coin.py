from bybit.exception import InvalidLimitPriceException
from bybit.models import Trader, Settings, EntryPrice
from pybit.unified_trading import HTTP
from bybit.utils import extract_symbol, extract_price, extract_side


def buy_coin_with_stop_loss(symbol, side):
    for account in Trader.objects.all():
        settings = account.settings
        print(settings)
        session = HTTP(
            api_key=account.api_key,
            api_secret=account.api_secret,
            demo=settings.demo
        )

        try:
            # Set leverage
            session.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=str(int(settings.leverage)),
                sellLeverage=str(int(settings.leverage)),
            )
        except Exception:
            pass

        # Get current market price
        market_data = session.get_tickers(category="linear", symbol=symbol)
        market_price = float(market_data['result']['list'][0]['lastPrice'])

        # print(market_data['result']['list'])
        qty_step = session.get_instruments_info(
            category="linear",
            symbol=symbol,
        )['result']['list'][0]['lotSizeFilter']['qtyStep']

        if '.' in qty_step:
            precision = len(qty_step.split('.')[1])
        else:
            precision = int(1 / len(qty_step)) - 1

        # Calculate quantity to buy based on amount in USD
        qty = settings.amount_usd / market_price
        qty = str(round(qty, precision))

        orders = [{
            'symbol': symbol,
            'side': side,
            'order_type': 'Market',
            'qty': qty,
            'time_in_force': "GTC"
        }]

        order = session.place_batch_order(category='linear', request=orders)
        check_order_msg(order)
        print(order)

        # Calculate stop loss price
        if side == "Buy":
            stop_loss_price = market_price * (1 - settings.stop_loss_percent / 100)
            take_profit_price = market_price * (1 + settings.take_profit_percent / 100)
        else:
            stop_loss_price = market_price * (1 + settings.stop_loss_percent / 100)
            take_profit_price = market_price * (1 - settings.take_profit_percent / 100)

        # Place stop loss order
        session.set_trading_stop(
            category='linear',
            symbol=symbol,
            side=side,
            stop_loss=str(stop_loss_price),
            take_profit=str(take_profit_price)
        )

        EntryPrice.objects.create(
            symbol=symbol,
            entry_price=market_price,
            side=side
        )


def check_order_msg(order):
    order_msg = order['retExtInfo']['list'][0]['msg']
    if order_msg != 'OK':
        print(order)
        raise InvalidLimitPriceException


def buy_coin_by_limit_price(symbol, side, price, tp=None, sl=None):
    for account in Trader.objects.all():
        settings = account.settings
        session = HTTP(
            api_key=account.api_key,
            api_secret=account.api_secret,
            demo=settings.demo
        )

        try:
            # Set leverage
            session.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=str(int(settings.leverage)),
                sellLeverage=str(int(settings.leverage)),
            )
        except Exception:
            pass

        qty_step = session.get_instruments_info(
            category="linear",
            symbol=symbol,
        )['result']['list'][0]['lotSizeFilter']['qtyStep']

        if '.' in qty_step:
            precision = len(qty_step.split('.')[1])
        else:
            precision = int(1 / len(qty_step)) - 1

        # Calculate quantity to buy based on amount in USD
        qty = settings.amount_usd / price
        qty = str(round(qty, precision))

        print(side)

        if side == "Buy":
            if tp is not None:
                take_profit_price = tp
            else:
                take_profit_price = price * (1 + settings.take_profit_percent / 100)

            if sl is not None:
                stop_loss_price = sl
            else:
                stop_loss_price = price * (1 - settings.stop_loss_percent / 100)

            triggerDirection = "1"
        else:
            if tp is not None:
                take_profit_price = tp
            else:
                take_profit_price = price * (1 - settings.take_profit_percent / 100)

            if sl is not None:
                stop_loss_price = sl
            else:
                stop_loss_price = price * (1 + settings.stop_loss_percent / 100)
            triggerDirection = "2"

        orders = [{
            'symbol': symbol,
            'side': side,
            'order_type': 'Limit',
            'qty': qty,
            'time_in_force': "GTC",
            'price': str(price),
            'stopLoss': str(stop_loss_price),
            "takeProfit": str(take_profit_price),
            "triggerDirection": triggerDirection,
            "triggerPrice": str(price),
        }]

        order = session.place_batch_order(category='linear', request=orders)
        check_order_msg(order)
        print(order)

        EntryPrice.objects.create(
            symbol=symbol,
            entry_price=price,
            side=side
        )


def close_position(symbol):
    for account in Trader.objects.all():
        settings = account.settings
        session = HTTP(
            api_key=account.api_key,
            api_secret=account.api_secret,
            demo=settings.demo
        )

        positions = session.get_positions(category="linear", symbol=symbol)
        positions = positions['result']['list']
        position_qty = 0

        for position in positions:
            position_qty += float(position['size'])

        if position_qty == 0:
            return

        close_qty = str(round(position_qty, 3))

        entry_price = EntryPrice.objects.filter(symbol=symbol).last()
        if entry_price.side == "Buy":
            close_side = "Sell"
        else:
            close_side = "Buy"

        orders = [{
            'symbol': symbol,
            'side': close_side,
            'order_type': 'Market',
            'qty': close_qty,
            'time_in_force': "GTC"
        }]

        order = session.place_batch_order(category='linear', request=orders)
        check_order_msg(order)


def change_tp_ls(message, tp, sl):
    for account in Trader.objects.all():
        settings = account.settings
        session = HTTP(
            api_key=account.api_key,
            api_secret=account.api_secret,
            demo=settings.demo
        )
        symbol = extract_symbol(message)
        order = session.get_positions(category="linear", symbol=symbol)
        side = extract_side(message)
        size = order['result']['list'][0]['size']

        if float(size) == 0:
            price = extract_price(message)
            close_order_by_symbol(symbol)
            buy_coin_by_limit_price(symbol, side, price, tp, sl)
        else:
            change_tp_ls_open_order(message, tp, sl)


def change_tp_ls_open_order(message, tp, sl):
    for account in Trader.objects.all():
        settings = account.settings
        session = HTTP(
            api_key=account.api_key,
            api_secret=account.api_secret,
            demo=settings.demo
        )

        symbol = extract_symbol(message)
        order = session.get_positions(category="linear", symbol=symbol)
        side = order['result']['list'][0]['side']
        mark_price = float(order['result']['list'][0]['markPrice'])

        print(order)

        if side == "Buy":
            if tp is not None:
                take_profit_price = tp
            else:
                take_profit_price = mark_price * (1 + settings.take_profit_percent / 100)

            if sl is not None:
                stop_loss_price = sl
            else:
                stop_loss_price = mark_price * (1 - settings.stop_loss_percent / 100)

        else:
            if tp is not None:
                take_profit_price = tp
            else:
                take_profit_price = mark_price * (1 - settings.take_profit_percent / 100)

            if sl is not None:
                stop_loss_price = sl
            else:
                stop_loss_price = mark_price * (1 + settings.stop_loss_percent / 100)

        session.set_trading_stop(
            category='linear',
            symbol=symbol,
            side=side,
            stop_loss=str(stop_loss_price),
            take_profit=str(take_profit_price),
        )


def close_order_by_symbol(symbol):
    for account in Trader.objects.all():
        settings = account.settings
        session = HTTP(
            api_key=account.api_key,
            api_secret=account.api_secret,
            demo=settings.demo
        )

        open_order = session.get_open_orders(category='linear', symbol=symbol)
        orders = open_order['result']['list']

        for order in orders:
            order_id = order['orderId']
            session.cancel_order(
                category="linear",
                symbol=symbol,
                orderId=order_id
            )
