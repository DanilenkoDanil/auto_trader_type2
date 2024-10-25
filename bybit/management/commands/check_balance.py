import os
import traceback
from datetime import time, datetime
import time as t

import django
from django.core.management import BaseCommand
from requests import session

from bybit.func_buy_coin import close_position_for_all_traders, get_positions_symbols_for_trader, close_position
from bybit.models import Trader, ErrorLog, GlobalSetting
from pybit.unified_trading import HTTP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rest.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()


def main():
    while True:
        print('Start')
        for account in Trader.objects.select_related('settings').all():
            try:
                settings = account.settings
                session = HTTP(
                    api_key=account.api_key,
                    api_secret=account.api_secret,
                    demo=settings.demo
                )

                response = session.get_wallet_balance(
                    accountType="UNIFIED",
                    coin="BTC",
                )
                total_balance = float(response['result']['list'][0]['totalEquity'])
                balanc1e = float(response['result']['list'][0]['totalMarginBalance'])
                balanc2e = float(response['result']['list'][0]['totalAvailableBalance'])
                print(str(total_balance) + " " + str(account))
                print(str(balanc1e) + " " + str(account))
                print(str(balanc2e) + " " + str(account))

                # check_balance(account, total_balance)
                check_balance(account, balanc1e)

                current = datetime.now()
                start = time(23, 30)
                end = time(23, 59)

                if start <= current.time() <= end:
                    write_balance(balanc1e, account.username)

            t.sleep(60)
        except Exception as e:
            # print(str(e))
            error_message = traceback.format_exc()
            print(error_message)


def check_balance(account, total_balance):
    global_sett = GlobalSetting.objects.last()
    rejection_perc = global_sett.switch_rejection
    reject_balance = float(account.balance) * (1 - rejection_perc / 100)
    print("balance" + str(account.balance))
    print("reject bal" + str(reject_balance))

    if total_balance <= reject_balance:
        global_sett.reaction = False
        global_sett.save()
        acc_symbols = get_positions_symbols_for_trader(account)
        for symbol in acc_symbols:
            close_position_for_all_traders(symbol, True)

        # for account in Trader.objects.select_related('settings').all():
            # acc_symbols = get_positions_symbols_for_trader(account)
            # for symbol in acc_symbols:
            #     close_position(account, symbol, True)


def write_balance(balance, trader_name):
    account = Trader.objects.filter(username=trader_name)
    account.balance = balance
    account.save()


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        try:
            main()
        except Exception as e:
            ErrorLog.objects.create(error=str(e))
