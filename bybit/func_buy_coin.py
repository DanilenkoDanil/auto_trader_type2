from bybit.models import Trader, Settings, EntryPrice
from pybit.unified_trading import HTTP


def buy_coin_with_stop_loss(symbol, side):
    settings = Settings.objects.last()
    for account in Trader.objects.all():
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
        precision = len(session.get_instruments_info(
            category="linear",
            symbol=symbol,
        )['result']['list'][0]['lotSizeFilter']['qtyStep'].split('.')[1])

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


def buy_coin_by_limit_price(symbol, side, price):
    settings = Settings.objects.last()
    for account in Trader.objects.all():
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

        precision = len(session.get_instruments_info(
            category="linear",
            symbol=symbol,
        )['result']['list'][0]['lotSizeFilter']['qtyStep'].split('.')[1])

        # Calculate quantity to buy based on amount in USD
        qty = settings.amount_usd / price
        qty = str(round(qty, precision))

        if side == "Buy":
            stop_loss_price = price * (1 - settings.stop_loss_percent / 100)
            take_profit_price = price * (1 + settings.take_profit_percent / 100)
        else:
            stop_loss_price = price * (1 + settings.stop_loss_percent / 100)
            take_profit_price = price * (1 - settings.take_profit_percent / 100)

        orders = [{
            'symbol': symbol,
            'side': side,
            'order_type': 'Limit',
            'qty': qty,
            'time_in_force': "GTC",
            'price': str(price),
            'stopLoss': str(stop_loss_price),
            "takeProfit": str(take_profit_price)
        }]

        order = session.place_batch_order(category='linear', request=orders)

        EntryPrice.objects.create(
            symbol=symbol,
            entry_price=price,
            side=side
        )


def close_position(symbol):
    settings = Settings.objects.last()
    for user in Trader.objects.all():
        session = HTTP(
            api_key=user.api_key,
            api_secret=user.api_secret,
            demo=settings.demo
        )

        positions = session.get_positions(category="linear", symbol=symbol)
        print(positions)

        entry_price = EntryPrice.objects.filter(symbol=symbol).last()

        position_qty = float(positions['result']['list'][0]['size'])

        close_qty = str(round(position_qty, 3))

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

        session.place_batch_order(category='linear', request=orders)


def change_tp_ls_order(message, take_profit, stop_loss):
    settings = Settings.objects.last()
    for user in Trader.objects.all():
        session = HTTP(
            api_key=user.api_key,
            api_secret=user.api_secret,
            demo=settings.demo
        )

        take_profit = float(take_profit)
        stop_loss = float(stop_loss)

        if take_profit is None:
            take_profit = settings.take_profit_percent
        if stop_loss is None:
            stop_loss = settings.stop_loss_percent

        symbol = message.split(" ")[0]
        symbol = symbol[1:] + "USDT"
        order = session.get_positions(category="linear", symbol=symbol)
        print(order)

        price = float(order['result']['list'][0]['markPrice'])
        side = order['result']['list'][0]['side']

        session.set_trading_stop(
            category='linear',
            symbol=symbol,
            side=side,
            stop_loss=str(stop_loss),
            take_profit=str(take_profit),
        )


def close_order_by_symbol(symbol):
    settings = Settings.objects.last()
    for user in Trader.objects.all():
        session = HTTP(
            api_key=user.api_key,
            api_secret=user.api_secret,
            demo=settings.demo
        )

    open_order = session.get_open_orders(category='linear', symbol=symbol)
    print(symbol)
    print(open_order)
    order_id = open_order['result']['list'][0]['orderId']

    print(session.cancel_order(
        category="linear",
        symbol=symbol,
        orderId=order_id
    ))
