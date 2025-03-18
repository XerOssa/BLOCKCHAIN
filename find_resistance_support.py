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
# Znalezienie lokalnych minimów i maksimów
# Znalezienie lokalnych minimów i maksimów
n = 5  # Szerokość okna do znajdowania ekstremów
min_indices = argrelextrema(df_selected['low'].values, np.less_equal, order=n)[0]
max_indices = argrelextrema(df_selected['high'].values, np.greater_equal, order=n)[0]

# Tworzenie nowych kolumn z wartościami wsparcia i oporu
df_selected['Support'] = np.nan
df_selected['Resistance'] = np.nan

df_selected.loc[df_selected.index[min_indices], 'Support'] = df_selected['low'].iloc[min_indices]
df_selected.loc[df_selected.index[max_indices], 'Resistance'] = df_selected['high'].iloc[max_indices]

# Tworzenie wykresu świecowego
fig = go.Figure(data=[go.Candlestick(x=df_selected['timestamp'],
                                    open=df_selected['open'],
                                    high=df_selected['high'],
                                    low=df_selected['low'],
                                    close=df_selected['close'],
                                    name='Candlestick Chart')])

# Dodawanie poziomów wsparcia i oporu
support_levels = df_selected['Support'].dropna().unique()
resistance_levels = df_selected['Resistance'].dropna().unique()

for level in support_levels:
    fig.add_trace(go.Scatter(x=df_selected['timestamp'], y=[level]*len(df_selected),
                             mode='lines', name=f'Support {level}',
                             line=dict(color='green', dash='dash')))

for level in resistance_levels:
    fig.add_trace(go.Scatter(x=df_selected['timestamp'], y=[level]*len(df_selected),
                             mode='lines', name=f'Resistance {level}',
                             line=dict(color='red', dash='dash')))

# Ustawienia wykresu
fig.update_layout(title=f'Wykres BTC/USDT z automatycznym wykrywaniem wsparć i oporów',
                  xaxis_title='Czas',
                  yaxis_title='Cena (USDT)',
                  xaxis_rangeslider_visible=False)

fig.show()






