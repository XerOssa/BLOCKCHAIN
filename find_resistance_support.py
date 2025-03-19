import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import argrelextrema


symbol = 'BTCUSDT'
interval = '1h'
limit = 1000
url = f'https://api.binance.com/api/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'

response = requests.get(url)
data = response.json()


# Konwertowanie na DataFrame
cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore']
df = pd.DataFrame(data, columns=cols)

df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df['close'] = pd.to_numeric(df['close'], errors='coerce')
df['high'] = pd.to_numeric(df['high'], errors='coerce')
df['low'] = pd.to_numeric(df['low'], errors='coerce')

df_selected = df.tail(200)


# Znalezienie lokalnych minimów i maksimów
n = 5  # Szerokość okna do znajdowania ekstremów

min_indices = argrelextrema(df_selected['low'].values, np.less_equal, order=n)[0]
max_indices = argrelextrema(df_selected['high'].values, np.greater_equal, order=n)[0]

# Tworzenie nowych kolumn z wartościami wsparcia i oporu
support_levels = df_selected.iloc[min_indices][['timestamp', 'low']]
resistance_levels = df_selected.iloc[max_indices][['timestamp', 'high']]


def filter_levels(levels):
    """
    Filtruje poziomy, pozostawiając tylko te, które są oddalone od siebie o co najmniej threshold (w procentach).
    """
    filtered = []
    previous_level = None

    for index, row in levels.iterrows():
        current_level = row[1]

        if previous_level is None or abs(current_level - previous_level) / previous_level :
            filtered.append(row)
            previous_level = current_level

    return pd.DataFrame(filtered, columns=levels.columns)


# Filtrowanie poziomów wsparcia i oporu
filtered_support = filter_levels(support_levels)
filtered_resistance = filter_levels(resistance_levels)


# Tworzenie wykresu świecowego
fig = go.Figure(data=[go.Candlestick(x=df_selected['timestamp'],
                                    open=df_selected['open'],
                                    high=df_selected['high'],
                                    low=df_selected['low'],
                                    close=df_selected['close'],
                                    name='Candlestick Chart')])


# Dodawanie poziomów wsparcia i oporu
for _, row in filtered_support.iterrows():
    fig.add_trace(go.Scatter(x=[row['timestamp']], y=[row['low']],
                             mode='markers', name='Support',
                             marker=dict(color='green', size=8)))

for _, row in filtered_resistance.iterrows():
    fig.add_trace(go.Scatter(x=[row['timestamp']], y=[row['high']],
                             mode='markers', name='Resistance',
                             marker=dict(color='red', size=8)))


# Ustawienia wykresu
fig.update_layout(title=f'Wykres BTC/USDT z przefiltrowanymi poziomami wsparć i oporów',
                  xaxis_title='Czas',
                  yaxis_title='Cena (USDT)',
                  xaxis_rangeslider_visible=False)

fig.show()
