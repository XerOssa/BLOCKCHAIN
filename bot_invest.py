
import os
import requests
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import matplotlib.dates as mdates
from dotenv import load_dotenv
from binance.client import Client
import hashlib
import hmac
import time

load_dotenv()

WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
API_KEY1 = os.getenv("API_KEY")
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")
BASE_URL = "https://api.binance.com"
client = Client(API_KEY, API_SECRET)

def adjust_quantity(symbol, price):
    # Pobieramy szczegóły symbolu
    info = client.get_symbol_info(symbol)
    
    # Znajdujemy filtr NOTIONAL i LOT_SIZE
    notional_filter = next(f for f in info['filters'] if f['filterType'] == 'NOTIONAL')
    lot_size_filter = next(f for f in info['filters'] if f['filterType'] == 'LOT_SIZE')

    min_notional = float(notional_filter['minNotional'])
    step_size = float(lot_size_filter['stepSize'])
    min_qty = float(lot_size_filter['minQty'])

    # Obliczamy minimalną ilość potrzebną, aby spełnić wymagania NOTIONAL
    required_quantity = max(min_qty, min_notional / price)

    # Zaokrąglamy ilość do najbliższego kroku (stepSize)
    quantity = int(required_quantity // step_size) * step_size
    return int(quantity)

# Przykład użycia
current_price = 0.068  # Aktualna cena DOGE w USDC (zmień na aktualną)
quantity = adjust_quantity('DOGEUSDC', current_price)
print(f"Ustalona ilość do zakupu: {quantity}")


def monitor_and_execute_grid(buy_orders, symbol, upper_price, lower_price, grid_levels, quantity):
    """Monitoruje realizację zleceń kupna i składa odpowiadające zlecenia sprzedaży."""
    while True:
        time.sleep(5)  # Sprawdzaj co 5 sekund

        for order in buy_orders[:]:  # Iteracja po kopii listy
            order_id = order['orderId']
            order_status = client.get_order(symbol=symbol, orderId=order_id)

            if order_status['status'] == "FILLED":
                buy_price = float(order_status['price'])
                sell_price = buy_price + (upper_price - lower_price) / (grid_levels - 1)

                # Sprawdź saldo, czy masz wystarczające środki do sprzedaży
                balance = client.get_asset_balance(asset="DOGE")  # Zmienna zależna od twojej pary (np. DOGE)
                available_balance = float(balance['free'])

                if available_balance >= quantity:
                    try:
                        # Składamy zlecenie sprzedaży
                        sell_order = client.order_limit_sell(
                            symbol=symbol,
                            quantity=quantity,
                            price=str(sell_price)
                        )
                        print(f"✅ Zrealizowano kupno na {buy_price} USDC -> Złożono sprzedaż na {sell_price} USDC")

                        # Usunięcie zrealizowanego zlecenia kupna z listy
                        buy_orders.remove(order)
                        # Dodanie zlecenia sprzedaży do listy
                        buy_orders.append(sell_order)
                    
                    except Exception as e:
                        print(f"Błąd przy składaniu zlecenia sprzedaży: {e}")
                else:
                    print(f"❌ Brak wystarczających środków na sprzedaż. Dostępne saldo: {available_balance} DOGE")
        
        time.sleep(5)  # Możesz zmniejszyć czas oczekiwania, jeśli chcesz częściej sprawdzać


def place_grid_orders(symbol, lower_price, upper_price, grid_levels, quantity):
    """Tworzy siatkę zleceń kupna, ale tylko jeśli nie zostały jeszcze zrealizowane."""
    grid_prices = [lower_price + i * (upper_price - lower_price) / (grid_levels - 1) for i in range(grid_levels)]
    print("Siatka cenowa:", grid_prices)

    buy_orders = []
    
    # Pobieramy informacje o symbolu
    info = client.get_symbol_info(symbol)
    
    # Sprawdzamy, czy mamy już aktywne zlecenie kupna
    active_orders = client.get_open_orders(symbol=symbol)
    
    if active_orders:
        print("Masz już aktywne zlecenie kupna. Nie będziemy składać nowych zleceń.")
        return buy_orders  # Jeśli są aktywne zlecenia, nie składamy nowych

    # Składaj nowe zlecenia, tylko jeśli nie mamy aktywnych
    for price in grid_prices:
        order = client.order_limit_buy(symbol=symbol, quantity=quantity, price=str(price))
        buy_orders.append(order)
        print(f"Złożono zlecenie KUPNA na {price} {symbol}")
    
    return buy_orders
