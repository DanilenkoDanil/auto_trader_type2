import time

from django.test import TestCase
from pybit.unified_trading import HTTP

from bybit.func_buy_coin import buy_coin_with_stop_loss, close_position
from bybit.models import Trader, Settings, EntryPrice


class BybitTestCase(TestCase):
    def setUp(self):
        settings = Settings.objects.create(stop_loss_percent=7, take_profit_percent=5, leverage=10, amount_usd=10, demo=True,
                                close_by_picture=True, close_by_stop=True)
        Trader.objects.create(username="me2", api_key="uWbeKMBymyV8IVuRdk",
                              api_secret="ItEjV75p0nsNlDZ5M5N0FMTMsmAwlaig3idV", balance=50, settings=settings)


    def test_close_position_by_picture(self):
        print(3)
        symbol = "ZECUSDT"
        side = "Sell"
        buy_coin_with_stop_loss(symbol, side)

        close_position(symbol, False)

        for account in Trader.objects.select_related('settings').all():
            settings = account.settings
            session = HTTP(
                testnet=False,
                api_key=account.api_key,
                api_secret=account.api_secret,
                demo=settings.demo
            )

            positions = session.get_positions(category="linear", symbol=symbol)
            response_position = positions['result']['list'][0]
            response_position_size = response_position['size']


            print(4)
            self.assertEqual(response_position_size, "0")


    def test_open_position_market(self):
        print(1)
        # #SUI market #SHORT
        symbol = "ZECUSDT"
        side = "Sell"

        buy_coin_with_stop_loss(symbol, side)

        for account in Trader.objects.select_related('settings').all():
            settings = account.settings
            session = HTTP(
                testnet=False,
                api_key=account.api_key,
                api_secret=account.api_secret,
                demo=settings.demo
            )

            positions = session.get_positions(category="linear", symbol=symbol)
            response_position = positions['result']['list'][0]

            response_side = response_position['side']

            self.assertEqual(side, response_side)

        close_position(symbol, False)




