import time
import pandas as pd
import ta
import os
from binance import Client


# KONFIGURACJA
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")
client = Client(API_KEY, API_SECRET)

TOP_LIMIT = 100  # Liczba najpopularniejszych kryptowalut do analizy
INTERVAL = '1h'  # Interwał świec (np. '1d', '4h', '1h')
RSI_PERIOD = 14
VOLUME_PERIOD = 21  # Liczba świec do wyliczenia średniego wolumenu


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
        data = data.iloc[:-1]
        return data
    except Exception as e:
        print(f'Błąd przy pobieraniu danych dla {symbol}: {e}')
        return None


def calculate_rsi(data):
    data['rsi'] = ta.momentum.RSIIndicator(data['close'], window=RSI_PERIOD).rsi()
    rsi_value = data.iloc[-1]['rsi']

    if pd.isna(rsi_value) or rsi_value <= 0 or rsi_value > 100:
        return None  # Ignoruj nieprawidłowe RSI

    return rsi_value


def check_volume_filter(data):
    last_volume = data.iloc[-1]['volume']
    average_volume = data['volume'].iloc[-VOLUME_PERIOD:].mean()
    return last_volume > average_volume


def main():
    top_symbols = get_top_cryptos()
    results = []

    for symbol in top_symbols:
        data = get_historical_klines(symbol, RSI_PERIOD + 1)

        if data is not None:
            rsi = calculate_rsi(data)
            if rsi is not None:  # Ignoruj nieprawidłowe RSI
                results.append((symbol, rsi))

        time.sleep(0.1)  # Uniknięcie przekroczenia limitów API

    # Posortowanie wyników po RSI rosnąco (najniższe na górze)
    sorted_results = sorted(results, key=lambda x: x[1])[:10]
    print('Najniższe RSI dla top 100 kryptowalut:')
    for symbol, rsi in sorted_results:
        print(f'{symbol}: RSI = {rsi}')
    # Sprawdzenie wolumenu tylko dla wybranych kryptowalut o najniższym RSI
    final_results = []
    for symbol, rsi in sorted_results:
        data = get_historical_klines(symbol, VOLUME_PERIOD)
        if data is not None and check_volume_filter(data):
            final_results.append((symbol, rsi))

    print('Najniższe RSI dla top 100 kryptowalut (z filtrem wolumenu):')
    for symbol, rsi in final_results:
        print(f'{symbol}: RSI = {rsi}')


if __name__ == '__main__':
    main()
