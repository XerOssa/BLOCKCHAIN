# Importowanie bibliotek
import requests
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas_ta as ta
import plotly.graph_objects as go
from scipy.signal import argrelextrema
from plotly.subplots import make_subplots




def fetch_data(symbol, interval, limit):
    url = f'https://api.binance.com/api/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()
    return pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])


def preprocess_data(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['low'] = pd.to_numeric(df['low'], errors='coerce')
    df['high'] = pd.to_numeric(df['high'], errors='coerce')
    return df


def find_sorted_support_resistance(df, n=40):
    # Wyszukaj minima i maksima
    min_indices = argrelextrema(df['low'].values, np.less_equal, order=n)[0]
    max_indices = argrelextrema(df['high'].values, np.greater_equal, order=n)[0]

    # Stwórz DataFrame dla wsparcia i oporu
    support_levels = df.iloc[min_indices][['timestamp', 'low']].copy()
    support_levels['type'] = 'support'  # Dodajemy typ poziomu

    resistance_levels = df.iloc[max_indices][['timestamp', 'high']].copy()
    resistance_levels['type'] = 'resistance'  # Dodajemy typ poziomu

    # Połącz oba DataFrame
    combined = pd.concat([support_levels, resistance_levels]).sort_values(by='timestamp')

    # Upewnijmy się, że wartości są naprzemienne
    sorted_levels = []
    last_type = None
    
    for i, row in combined.iterrows():
        if last_type != row['type']:  # Jeśli typ poziomu zmienia się, dodajemy go
            sorted_levels.append(row)
            last_type = row['type']
    
    # Zwróć wynik jako DataFrame
    return pd.DataFrame(sorted_levels)



def calculate_support_resistance_difference(df, support_resistance_df):
    # Oblicz średnią cenę zamknięcia
    avg_price = df['close'].mean()

    # Tworzymy listę różnic między oporem a wsparciem
    differences = []
    
    # Iterujemy po poziomach
    for i in range(1, len(support_resistance_df)):
        if support_resistance_df.iloc[i-1]['type'] == 'support' and support_resistance_df.iloc[i]['type'] == 'resistance':
            support = support_resistance_df.iloc[i-1]
            resistance = support_resistance_df.iloc[i]
            
            # Oblicz różnicę między oporem a wsparciem
            difference = resistance['high'] - support['low']
            
            # Jeżeli różnica jest większa niż 5% średniej ceny
            if difference / avg_price > 0.05:
                differences.append({
                    'support_time': support['timestamp'],
                    'resistance_time': resistance['timestamp'],
                    'support_level': support['low'],
                    'resistance_level': resistance['high'],
                    'difference': difference
                })

    return pd.DataFrame(differences)



def find_extremums_sorted(df, n=5):
    min_indices = argrelextrema(df['low'].values, np.less_equal, order=n)[0]
    max_indices = argrelextrema(df['high'].values, np.greater_equal, order=n)[0]

    support_levels = df.iloc[min_indices][['timestamp', 'low']].sort_values(by='low')
    resistance_levels = df.iloc[max_indices][['timestamp', 'high']].sort_values(by='high', ascending=False)
    
    return support_levels, resistance_levels    


def calculate_indicators(df):
    df['RSI'] = ta.rsi(df['close'], length=20)
    df['EMA_9'] = ta.ema(df['close'], length=9)
    df['EMA_25'] = ta.ema(df['close'], length=25)
    return df.dropna()


def find_levels(df, n=5):
    min_indices = argrelextrema(df['low'].values, np.less_equal, order=n)[0]
    max_indices = argrelextrema(df['high'].values, np.greater_equal, order=n)[0]

    support_levels = df.iloc[min_indices][['timestamp', 'low']]
    resistance_levels = df.iloc[max_indices][['timestamp', 'high']]
    return support_levels, resistance_levels


def plot_chart(df, symbol):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.1, row_heights=[0.7, 0.3])

    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Candlestick Chart'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['RSI'],
        mode='lines',
        name='RSI',
        line=dict(color='blue')
    ), row=2, col=1)

    fig.update_layout(title=f'Candlestick Chart for {symbol}',
                      xaxis_title='Time',
                      yaxis_title='Price (USDC)',
                      xaxis_rangeslider_visible=False)
    fig.show()


def train_model(X_train, y_train):
    model = lgb.LGBMClassifier(n_estimators=100, learning_rate=0.05, num_leaves=31)
    model.fit(X_train, y_train)
    return model


def prepare_features(df):
    scaler = StandardScaler()
    features = ['close', 'volume', 'EMA_9', 'EMA_25', 'RSI']
    df[features] = scaler.fit_transform(df[features])
    return df, scaler


def main():
    symbol = 'BTCUSDC'
    interval = '15m'
    limit = 1000

    df = fetch_data(symbol, interval, limit)
    df = preprocess_data(df)
    df = calculate_indicators(df)
    support_resistance_df = find_sorted_support_resistance(df)

    # Oblicz różnice i wybierz te, które mają różnicę większą niż 5% średniej ceny
    differences_df = calculate_support_resistance_difference(df, support_resistance_df)
    
    print(differences_df)
    plot_chart(df, symbol)
    


    # Przygotowanie danych dla LightGBM
    df, scaler = prepare_features(df)

    X = df[['close', 'volume', 'EMA_9', 'EMA_25', 'RSI']]
    y = (df['close'].pct_change() > 0).astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = train_model(X_train, y_train)

    # Ocena modelu
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f'Accuracy: {accuracy:.4f}')


if __name__ == "__main__":
    main()
