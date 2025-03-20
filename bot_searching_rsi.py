import time
import pandas as pd
import pandas_ta as ta
import os
from binance import Client
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytz


# KONFIGURACJA
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")
client = Client(API_KEY, API_SECRET)

TOP_LIMIT = 100  # Liczba najpopularniejszych kryptowalut do analizy
INTERVAL = '1h'  # Interwał świec (np. '1d', '4h', '1h')
RSI_PERIOD = 14
VOLUME_PERIOD = 21  # Liczba świec do wyliczenia średniego wolumenu
MAX_WORKERS = 10  # Liczba wątków do równoległego przetwarzania
LOCAL_TZ = pytz.timezone('Europe/Warsaw')  # Strefa czasowa +1


def get_top_cryptos():
    tickers = client.get_ticker()
    sorted_tickers = sorted(tickers, key=lambda x: float(x['quoteVolume']), reverse=True)
    top_symbols = [x['symbol'] for x in sorted_tickers if x['symbol'].endswith('USDC')][:TOP_LIMIT]
    return top_symbols


def get_historical_klines(symbol, limit):
    try:
        klines = client.get_klines(symbol=symbol, interval=INTERVAL, limit=limit)
        data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                             'close_time', 'quote_asset_volume', 'number_of_trades',
                                             'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        data['close'] = data['close'].astype(float)
        data['volume'] = data['volume'].astype(float)
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert(LOCAL_TZ)
        data = data.iloc[:-1]
        return data
    except Exception as e:
        print(f'Błąd przy pobieraniu danych dla {symbol}: {e}')
        return None


def analyze_symbol(symbol):
    data = get_historical_klines(symbol, max(RSI_PERIOD + 1, VOLUME_PERIOD))
    if data is None:
        return None

    # Oblicz RSI
    data['rsi'] = ta.rsi(data['close'], length=RSI_PERIOD)
    rsi_value = data.iloc[-1]['rsi']
    rsi_date = data.iloc[-1]['timestamp']

    if pd.isna(rsi_value) or rsi_value <= 0 or rsi_value > 100:
        return None

    # Sprawdzenie wolumenu
    last_volume = data.iloc[-1]['volume']
    average_volume = data['volume'].iloc[-VOLUME_PERIOD:].mean()

    if last_volume > average_volume:
        return symbol, rsi_value, rsi_date

    return None


def main():
    top_symbols = get_top_cryptos()
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_symbol = {executor.submit(analyze_symbol, symbol): symbol for symbol in top_symbols}

        for future in as_completed(future_to_symbol):
            result = future.result()
            if result:
                results.append(result)

    # Posortowanie wyników po RSI rosnąco (najniższe na górze)
    sorted_results = sorted(results, key=lambda x: x[1])[:10]

    print('Najniższe RSI dla top 100 kryptowalut (z filtrem wolumenu):')
    for symbol, rsi, rsi_date in sorted_results:
        print(f'{symbol}: RSI = {round(rsi, 2)} (Data: {rsi_date})')


if __name__ == '__main__':
    main()
