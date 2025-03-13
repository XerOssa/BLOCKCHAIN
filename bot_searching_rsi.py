import os
import time
import pandas as pd
import ta
from binance import Client


# KONFIGURACJA
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")

client = Client(API_KEY, API_SECRET)

TOP_LIMIT = 300
INTERVAL = '4h'
RSI_PERIOD = 21


def get_top_cryptos():
    tickers = client.get_ticker()
    sorted_tickers = sorted(tickers, key=lambda x: float(x['quoteVolume']), reverse=True)
    top_symbols = [x['symbol'] for x in sorted_tickers if x['symbol'].endswith('USDC')][:TOP_LIMIT]
    return top_symbols


def get_historical_klines(symbol):
    try:
        klines = client.get_klines(symbol=symbol, interval=INTERVAL, limit=RSI_PERIOD+1)
        data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                                             'close_time', 'quote_asset_volume', 'number_of_trades', 
                                             'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        data['close'] = data['close'].astype(float)
        return data
    except Exception as e:
        print(f'Błąd przy pobieraniu danych dla {symbol}: {e}')
        return None


def calculate_rsi(data):
    data['rsi'] = ta.momentum.RSIIndicator(data['close'], window=RSI_PERIOD).rsi()
    return data.iloc[-1]['rsi']


def main():
    top_symbols = get_top_cryptos()
    results = []

    for symbol in top_symbols:
        data = get_historical_klines(symbol)

        if data is not None:
            rsi = calculate_rsi(data)
            if pd.notna(rsi):
                results.append((symbol, rsi))
        
        time.sleep(0.1)  # Uniknięcie przekroczenia limitów API

    # Posortowanie wyników po RSI rosnąco (najniższe na górze)
    sorted_results = sorted(results, key=lambda x: x[1])

    print('Najniższe RSI dla top 500 kryptowalut:')
    for symbol, rsi in sorted_results[:10]:  # Wyświetlanie 10 kryptowalut o najniższym RSI
        print(f'{symbol}: RSI = {rsi}')


if __name__ == '__main__':
    main()
