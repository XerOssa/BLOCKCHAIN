import requests
import pandas as pd
import pandas_ta as ta
import time
import schedule

def get_binance_BNB(symbol="BNBUSDT", interval="5m", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "_", "_", "_", "_", "_", "_"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")  # Konwersja na datę
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)  # Zamiana na liczby
    return df

# df = get_binance_BNB()


def get_price(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    return float(data["price"])


def calculate_rsi(prices, length=14):
    df = pd.DataFrame(prices, columns=["close"])
    df["rsi"] = ta.rsi(df["close"], length=length)
    return df["rsi"].iloc[-1]  # Ostatnia wartość RSI

# Przykładowe ceny (możesz pobierać je z API)
def get_historical_prices(symbol="BTCUSDT", interval="5m", limit=14):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    close_prices = [float(candle[4]) for candle in data]  # Indeks 4 = cena zamknięcia
    return close_prices

prices = get_historical_prices()  # Pobranie ostatnich 14 cen zamknięcia



def trading_strategy(price, rsi):
    if rsi < 30:  # RSI poniżej 30 = rynek wyprzedany (można kupować)
        return "BUY"
    elif rsi > 70:  # RSI powyżej 70 = rynek wykupiony (można sprzedawać)
        return "SELL"
    return "HOLD"

rsi_value = calculate_rsi(prices)
current_price = get_price()
decision = trading_strategy(current_price, rsi_value)
print(f"RSI: {rsi_value}, Decyzja: {decision}")


def run_bot():
    price = get_price()
    rsi = calculate_rsi(prices)
    decision = trading_strategy(price, rsi)
    print(f"Cena: {price}, RSI: {rsi}, Decyzja: {decision}")

schedule.every(5).minutes.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)

