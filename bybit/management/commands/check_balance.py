import os
from datetime import time
import time as t

import django
from django.core.management import BaseCommand

from bybit.models import Trader, ErrorLog, GlobalSetting
from pybit.unified_trading import HTTP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rest.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()


def main():
    while True:
        print('Start')
        try:
            for account in Trader.objects.select_related('settings').all():
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
                total_balance = response['result']['list'][0]['totalWalletBalance']
                print(total_balance + " " + str(account))

                check_balance(account, total_balance)

                current = t.localtime()
                start = time(23, 30)
                end = time(23, 59)

                if start <= current <= end:
                    write_balance(total_balance, account.username)

            t.sleep(600)

        except Exception as e:
            print(str(e))


def check_balance(account, total_balance):
    global_sett = GlobalSetting.objects.last()
    rejection_perc = global_sett.switch_rejection
    reject_balance = account.balance * rejection_perc / 100
    if total_balance <= reject_balance:
        global_sett.reaction = False
        global_sett.save()


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
