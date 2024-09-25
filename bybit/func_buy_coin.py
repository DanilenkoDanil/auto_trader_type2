from bybit.models import Trader, EntryPrice
from pybit.unified_trading import HTTP
from bybit.utils import extract_symbol, extract_price, extract_side, calculate_tp_sl_price, check_order_msg


def buy_coin_with_stop_loss(symbol, side):
    for account in Trader.objects.select_related('settings').all():
        settings = account.settings
        print(settings)
        session = HTTP(
            api_key=account.api_key,
            api_secret=account.api_secret,
            demo=settings.demo
        )

        try:
            session.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=str(int(settings.leverage)),
                sellLeverage=str(int(settings.leverage)),
            )
        except Exception:
            pass

        market_data = session.get_tickers(category="linear", symbol=symbol)
        market_price = float(market_data['result']['list'][0]['lastPrice'])

        qty_step = session.get_instruments_info(
            category="linear",
            symbol=symbol,
        )['result']['list'][0]['lotSizeFilter']['qtyStep']

        if '.' in qty_step:
            precision = len(qty_step.split('.')[1])
        else:
            precision = int(1 / len(qty_step)) - 1

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

        stop_loss_price, take_profit_price, trigger_direction = calculate_tp_sl_price(side, market_price,
                                    settings.stop_loss_percent, settings.take_profit_percent, None, None)

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





def buy_coin_by_limit_price(symbol, side, price, tp=None, sl=None):
    for account in Trader.objects.select_related('settings').all():
        settings = account.settings
        session = HTTP(
            api_key=account.api_key,
            api_secret=account.api_secret,
            demo=settings.demo
        )

        try:
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

        qty = settings.amount_usd / price
        qty = str(round(qty, precision))

        stop_loss_price, take_profit_price, trigger_direction = calculate_tp_sl_price(side, price,
                                                    settings.stop_loss_percent, settings.take_profit_percent, sl, tp)

        orders = [{
            'symbol': symbol,
            'side': side,
            'order_type': 'Limit',
            'qty': qty,
            'time_in_force': "GTC",
            'price': str(price),
            'stopLoss': str(stop_loss_price),
            "takeProfit": str(take_profit_price),
            "triggerDirection": trigger_direction,
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


def close_position(symbol, stop_exists):
    for account in Trader.objects.select_related('settings').all():
        settings = account.settings
        if stop_exists:
            if not settings.close_by_stop:
                continue
        else:
            if not settings.close_by_picture:
                continue

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

        positions = session.get_positions(category="linear", symbol=symbol)
        positions = positions['result']['list']
        print("POSITIONS")
        print(positions)


def change_tp_ls(message, tp, sl):
    for account in Trader.objects.select_related('settings').all():
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
    for account in Trader.objects.select_related('settings').all():
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

        stop_loss_price, take_profit_price, trigger_direction = calculate_tp_sl_price(side, mark_price,
                                                 settings.stop_loss_percent, settings.take_profit_percent, sl, tp)

        session.set_trading_stop(
            category='linear',
            symbol=symbol,
            side=side,
            stop_loss=str(stop_loss_price),
            take_profit=str(take_profit_price),
        )


def close_order_by_symbol(symbol):
    for account in Trader.objects.select_related('settings').all():
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
