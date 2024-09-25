from django.test import TestCase
from pybit.unified_trading import HTTP

from bybit.func_buy_coin import buy_coin_with_stop_loss, close_position
from bybit.models import Trader, Settings, EntryPrice


class BybitTestCase(TestCase):
    def setUp(self):
        settings = Settings.objects.create(stop_loss_percent=7, take_profit_percent=5, leverage=10, amount_usd=10, demo=False,
                                close_by_picture=True, close_by_stop=True)
        Trader.objects.create(username="me2", api_key="Kw9H8JonPhoineC4Bm",
                              api_secret="kY3I2QiJtGc8fmKqIzwWxg9LtWmWEiAZi941", balance=10, settings=settings)


    def test_open_position_market(self):
        # #SUI market #SHORT
        symbol = "CKBUSDT"
        side = "Sell"

        buy_coin_with_stop_loss(symbol, side)

        for account in Trader.objects.select_related('settings').all():
            settings = account.settings
            session = HTTP(
                api_key=account.api_key,
                api_secret=account.api_secret,
                demo=settings.demo
            )

            positions = session.get_positions(category="linear", symbol=symbol)
            response_position = positions['result']['list'][0]

            response_side = response_position['side']

            self.assertEqual(side, response_side)


    def test_close_position_by_picture(self):
        symbol = "CKBUSDT"
        side = "Sell"
        EntryPrice.objects.create(symbol=symbol, side=side, entry_price=16)
        # buy_coin_with_stop_loss(symbol, side)

        close_position(symbol, False)

        for account in Trader.objects.select_related('settings').all():
            settings = account.settings
            session = HTTP(
                api_key=account.api_key,
                api_secret=account.api_secret,
                demo=settings.demo
            )

            positions = session.get_positions(category="linear", symbol=symbol)
            response_position = positions['result']['list']
            print(positions)
            number_pos = 0
            for position in response_position:
                number_pos += 1

            self.assertEqual(number_pos, 0)


