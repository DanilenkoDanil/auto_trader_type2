from bybit.exception import InvalidLimitPriceException


def extract_symbol(message):
    symbol = message.split(" ")[0]
    symbol = symbol[1:] + "USDT"
    return symbol


def extract_price(message):
    words = message.split(" ")
    price = float(words[1])
    return price


def extract_side(message):
    if "LONG" in message:
        return "Buy"
    else:
        return "Sell"


def check_order_msg(order):
    order_msg = order['retExtInfo']['list'][0]['msg']
    if order_msg != 'OK':
        print(order)
        raise InvalidLimitPriceException


def calculate_tp_sl_price(side, price, sett_sl_perc, sett_tp_perc, new_sl, new_tp):
    take_profit_price = new_tp if new_tp is not None else price * (
        1 + (sett_tp_perc / 100) if side == "Buy" else 1 - sett_tp_perc / 100)

    stop_loss_price = new_sl if new_sl is not None else price * (
        1 - (sett_sl_perc / 100) if side == "Buy" else 1 + sett_sl_perc / 100)

    trigger_direction = "1" if side == "Buy" else "2"

    return stop_loss_price, take_profit_price, trigger_direction


def calculate_precision(info):
    qty_step = info['result']['list'][0]['lotSizeFilter']['qtyStep']
    if '.' in qty_step:
        precision = len(qty_step.split('.')[1])
    else:
        precision = int(1 / len(qty_step)) - 1

    return precision


def extract_position_qty(positions):
    positions = positions['result']['list']
    position_qty = 0
    for position in positions:
        position_qty += float(position['size'])
    return position_qty
