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
