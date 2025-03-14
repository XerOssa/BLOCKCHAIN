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
INTERVAL = '1h'
RSI_PERIOD = 14
VOLUME_PERIOD = 21  # Liczba świec do wyliczenia średniego wolumenu
PRICE_ACTION_PERIOD = 20  # Liczba świec do analizy Price Action
PRICE_ACTION_THRESHOLD = 0.05  # 5% - akceptowalny dystans od minimum


def get_top_cryptos():
    tickers = client.get_ticker()
    sorted_tickers = sorted(tickers, key=lambda x: float(x['quoteVolume']), reverse=True)
    top_symbols = [x['symbol'] for x in sorted_tickers if x['symbol'].endswith('USDC')][:TOP_LIMIT]
    return top_symbols


def get_historical_klines(symbol):
    try:
        klines = client.get_klines(symbol=symbol, interval=INTERVAL, limit=max(RSI_PERIOD, VOLUME_PERIOD, PRICE_ACTION_PERIOD))
        data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                                             'close_time', 'quote_asset_volume', 'number_of_trades', 
                                             'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        data['close'] = data['close'].astype(float)
        data['volume'] = data['volume'].astype(float)
        data['low'] = data['low'].astype(float)
        return data
    except Exception as e:
        print(f'Błąd przy pobieraniu danych dla {symbol}: {e}')
        return None


def calculate_rsi(data):
    data['rsi'] = ta.momentum.RSIIndicator(data['close'], window=RSI_PERIOD).rsi()
    return data.iloc[-1]['rsi']


def check_volume_filter(data):
    last_volume = data.iloc[-1]['volume']
    average_volume = data['volume'].iloc[-VOLUME_PERIOD:].mean()
    return last_volume > average_volume


def check_price_action(data):
    current_price = data.iloc[-1]['close']
    
    # Znajdź minimalną cenę z ostatnich PRICE_ACTION_PERIOD świec
    recent_min = data['low'].iloc[-PRICE_ACTION_PERIOD:].min()
    
    # Oblicz średnią cenę z ostatnich PRICE_ACTION_PERIOD świec
    recent_average = data['close'].iloc[-PRICE_ACTION_PERIOD:].mean()
    
    # Sprawdź, czy cena jest blisko ostatniego minimum (poniżej progu PRICE_ACTION_THRESHOLD)
    near_minimum = (current_price <= recent_min * (1 + PRICE_ACTION_THRESHOLD))
    
    # Sprawdź, czy cena jest niższa niż średnia cena
    below_average = (current_price < recent_average)
    
    return near_minimum or below_average  # Zwróć True jeśli którykolwiek warunek jest spełniony


def main():
    top_symbols = get_top_cryptos()
    results = []
    
    for symbol in top_symbols:
        data = get_historical_klines(symbol)
        
        if data is not None:
            rsi = calculate_rsi(data)
            
            if pd.notna(rsi):
                if check_volume_filter(data) and check_price_action(data):  # Sprawdzamy dodatkowo Price Action
                    results.append((symbol, rsi))
        
        time.sleep(0.1)

    sorted_results = sorted(results, key=lambda x: x[1])

    print('Najniższe RSI dla top 300 kryptowalut (z filtrem wolumenu i Price Action):')
    for symbol, rsi in sorted_results[:10]:
        print(f'{symbol}: RSI = {rsi}')


if __name__ == '__main__':
    main()
