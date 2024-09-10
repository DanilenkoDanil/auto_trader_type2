import traceback

from bybit.models import Chat, ErrorLog
from bybit.func_buy_coin import buy_coin_with_stop_loss, buy_coin_by_limit_price, \
    change_tp_ls, close_position, close_order_by_symbol
from bybit.utils import extract_symbol, extract_price

from django.core.management.base import BaseCommand
from telethon.sync import TelegramClient
from telethon import events
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rest.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()


def main():
    print('Start')
    client = TelegramClient(
        "session",
        2547559,
        "1a1975ef3b460f054d2777ddf45e8faf"
    )
    client.start()
    client.get_dialogs()

    @client.on(events.NewMessage())
    async def handler_first(event):
        try:
            chats_list = []
            for chat in Chat.objects.all():
                chats_list.append(str(chat.chat_id).replace('-', '')[3:])

            print('New_message')
            try:
                have_channel_id = getattr(event.message.peer_id, 'channel_id', False)
                if have_channel_id and str(event.message.peer_id.channel_id) in chats_list:
                    print('1')
                    message = str(event.message.message)
                    print(message)

                    if "SHORT" in message or "LONG" in message:
                        print('2')
                        words = message.split(" ")

                        symbol = extract_symbol(message)

                        if "LONG" in message:
                            side = "Buy"
                        else:
                            side = "Sell"

                        if len(words) == 3:
                            price = float(words[1])
                            buy_coin_by_limit_price(symbol, side, price)
                        elif len(words) == 2:
                            buy_coin_with_stop_loss(symbol, side)

                    elif event.message.reply_to_msg_id and ("TP" in message or "SL" in message):
                        print('3')
                        reply_message = await event.message.get_reply_message()

                        if "TP" in message:
                            tp = message.split("TP")[1].split("\n")[0][3:]
                        else:
                            tp = None
                        if "SL" in message:
                            sl = message.split("SL")[1][3:]
                        else:
                            sl = None

                        change_tp_ls(reply_message.text, tp, sl)

                    elif event.message.photo and event.message.reply_to_msg_id:
                        print('4')
                        reply_message = await event.message.get_reply_message()
                        print(reply_message.text)
                        symbol = extract_symbol(reply_message.text)
                        close_position(symbol)

                    elif "cancel" in message.lower():
                        print('5')
                        reply_message = await event.message.get_reply_message()
                        print(reply_message.text)
                        symbol = extract_symbol(reply_message.text)
                        close_order_by_symbol(symbol)

            except AttributeError:
                error_message = traceback.format_exc()
                ErrorLog.objects.create(error=error_message)
        except Exception as e:
            error_message = traceback.format_exc()
            ErrorLog.objects.create(error=error_message)
            # ErrorLog.objects.create(error=str(e))
    client.run_until_disconnected()


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        try:
            main()
        except Exception as e:
            ErrorLog.objects.create(error=str(e))
