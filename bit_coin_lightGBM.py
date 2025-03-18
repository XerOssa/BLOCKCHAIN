import requests
import pandas as pd
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas_ta as ta
import plotly.graph_objects as go

# Pobieranie danych BTC/USDT z Binance
symbol = 'BTCUSDT'
interval = '1h'  # interwał 1 godzina
limit = 1000  # liczba punktów danych

url = f'https://api.binance.com/api/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'

response = requests.get(url)
data = response.json()

# Konwertowanie na DataFrame
df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])

# Konwersja timestamp na datę
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')


# Wybór fragmentu zbioru danych (ostatnich 200 godzin)
df_selected = df.tail(200)

# Obliczanie poziomu wsparcia (najniższa cena) i oporu (najwyższa cena)
support_level = df_selected['low'].min()  # Najniższa cena w okresie
resistance_level = df_selected['high'].max()  # Najwyższa cena w okresie

# Tworzenie wykresu świecowego za pomocą Plotly
fig = go.Figure(data=[go.Candlestick(
    x=df_selected['timestamp'],
    open=df_selected['open'],
    high=df_selected['high'],
    low=df_selected['low'],
    close=df_selected['close'],
    name='Candlestick Chart'
)])

fig.add_trace(go.Scatter(
    x=df_selected['timestamp'],
    y=[resistance_level] * len(df_selected), 
    mode='lines',
    name='Resistance',
    line=dict(color='red', dash='dash')
))

fig.add_trace(go.Scatter(
    x=df_selected['timestamp'],
    y=[support_level] * len(df_selected),
    mode='lines',
    name='Support',
    line=dict(color='green', dash='dash')
))

# Ustawienia wykresu
fig.update_layout(
    title=f'Candlestick Chart for {symbol} - Last 200 Hours with Support and Resistance Levels',
    xaxis_title='Time',
    yaxis_title='Price (USDT)',
    xaxis_rangeslider_visible=False  # Ukrywa suwak na osi X
)

# Wyświetlenie wykresu
fig.show()

df['close'] = pd.to_numeric(df['close'], errors='coerce')

# Obliczanie dziennej zmiany ceny
df['price_change'] = df['close'].pct_change()

# Tworzenie etykiety (0 - spadek, 1 - wzrost) dla kierunku zmiany ceny
df['target'] = (df['price_change'] > 0).astype(int)

# Używamy danych z poprzednich dni (lag features), np. średnia ruchoma
df['SMA_5'] = df['close'].rolling(window=5).mean()
df['SMA_20'] = df['close'].rolling(window=20).mean()
df['rsi'] = ta.rsi(df['close'], length=14)

# Usuwanie wierszy z brakującymi danymi
df = df.dropna()

# Normalizacja cech
scaler = StandardScaler()
features = ['close', 'volume', 'SMA_5', 'SMA_20', 'rsi']
df[features] = scaler.fit_transform(df[features])

# Oddzielamy cechy i etykiety
X = df[features]
y = df['target']

# Podział danych na zbiór treningowy i testowy
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Tworzymy i trenujemy model LightGBM
model = lgb.LGBMClassifier(n_estimators=100, learning_rate=0.05, num_leaves=31)
model.fit(X_train, y_train)

# Predykcja na zbiorze testowym
y_pred = model.predict(X_test)

# Ocena modelu
accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy: {accuracy:.4f}')

# Pobieranie nowych danych BTC/USDT (np. z ostatnich 100 punktów danych)
url_new = f'https://api.binance.com/api/v1/klines?symbol={symbol}&interval={interval}&limit=200'
response_new = requests.get(url_new)
new_data = response_new.json()

# Konwertowanie nowych danych na DataFrame
new_data_df = pd.DataFrame(new_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])

# Konwersja timestamp na datę
new_data_df['timestamp'] = pd.to_datetime(new_data_df['timestamp'], unit='ms')

# Konwersja kolumny 'close' na typ numeryczny
new_data_df['close'] = pd.to_numeric(new_data_df['close'], errors='coerce')

# Sortowanie nowych danych po czasie
new_data_df = new_data_df.sort_values('timestamp')

# Obliczanie SMA i RSI dla nowych danych
new_data_df['SMA_5'] = new_data_df['close'].rolling(window=5).mean()
new_data_df['SMA_20'] = new_data_df['close'].rolling(window=20).mean()
new_data_df['rsi'] = ta.rsi(new_data_df['close'], length=14)

# Usuwanie brakujących danych
new_data_df = new_data_df.dropna()

# Normalizowanie nowych danych
new_data_df[features] = scaler.transform(new_data_df[features])

# Prognozowanie kierunku zmiany ceny
predictions = model.predict(new_data_df[features])

# Wyświetlenie prognoz (0 - spadek, 1 - wzrost)
print(predictions)

