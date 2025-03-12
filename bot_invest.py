
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


def get_binance_data(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    return float(data["price"]) if "price" in data else None


def get_wallet_balance(wallet_address, api_key):
    url = f"https://api.bscscan.com/api?module=account&action=balance&address={wallet_address}&tag=latest&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    if data["status"] == "1":
        balance_wei = int(data["result"])
        return balance_wei / 10**18
    else:
        print(f"Błąd: {data['message']}")
        return None


def plot_total_balance():
    df1 = pd.read_csv("balance_data.csv")
    df1['Date'] = pd.to_datetime(df1['Date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df1['Date'] = pd.to_datetime(df1['Date'], errors='coerce')
    
    df1 = df1.dropna(subset=['Date'])
    plt.clf()
    plt.plot(df1['Date'], df1['Total'], marker='o', linestyle='-', color='b', label='Total Balance (PLN)')
    plt.plot(df1['Date'], df1['Deposit'], marker='o', linestyle='-', color='r', label='Deposit')
    plt.title('Total Balance Over Time', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Total Balance (PLN)', fontsize=12)
    data_size = len(df1)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    if data_size <= 10:
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
    elif data_size <= 30:
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    else:
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.gca().xaxis.set_minor_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()


def save_to_csv(date, bnbusdt, usd, saldo_bnb, saldo_sol,  saldo_eth, total, deposit):
    
    file_exists = False
    # date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    try:
        with open('balance_data.csv', 'r'):
            file_exists = True
    except FileNotFoundError:
        pass
    with open('balance_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            writer.writerow(['Date', 'BNB/USDT', 'USD/PLN', 'Saldo_bnb', 'Saldo_sol', 'saldo_eth','Total', 'Deposit'])
        
        writer.writerow([date, bnbusdt, usd, saldo_bnb, saldo_sol, saldo_eth, total, deposit])



def get_investments(balance):
    investments = []
    
    for asset in balance['balances']:
        symbol = asset['asset']
        free = float(asset['free'])  # Dostępne środki
        locked = float(asset['locked'])  # Zablokowane środki
        
        # Jeśli mamy jakiekolwiek środki (zarówno free, jak i locked), dodajemy je do listy
        if free > 0 or locked > 0:
            investments.append({
                'symbol': symbol,
                'free': free,
                'locked': locked,
                'total': free + locked  # Całkowita wartość aktywów
            })
    
    return investments


def get_staking_balance(client):
    url = "https://api.binance.com/sapi/v1/staking/position"
    
    # Wprowadź swoje dane API, które są wymagane do autoryzacji
    params = {
        'timestamp': int(time.time() * 1000),  # Wartość timestamp w milisekundach
        'recvWindow': 5000,  # Opcjonalnie, można dodać parametry
        'product': 'STAKING'
    }
    
    # Tworzymy podpis (signature) na podstawie parametrów zapytania
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(
        client.API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    params['signature'] = signature  # Dodajemy podpis do parametrów zapytania

    headers = {
        'X-MBX-APIKEY': client.API_KEY  # Wstaw swój klucz API
    }
    
    # Wykonanie zapytania
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        for item in data:
            item_asset = item['asset']
            item_amount = float(item['amount'])
    else:
        print(f"Error: {response.status_code} - {response.text}")
    return item_amount


def get_binance_balance(client):
    try:
        account_info = client.get_account()
        balances = account_info.get("balances", [])

        assets = []
        for asset in balances:
            asset_name = asset["asset"]
            free = float(asset["free"])
            locked = float(asset["locked"])
            total = free + locked

            if total > 0:  # Ignorujemy aktywa o zerowym saldzie
                assets.append({
                    "asset": asset_name,
                    "free": free,
                    "locked": locked,
                    "total": total
                })

        return assets
    except Exception as e:
        print(f"Błąd podczas pobierania salda: {e}")
        return []



def main():

    balance_bnb = get_wallet_balance(WALLET_ADDRESS, API_KEY1)
    bnbusdt = get_binance_data(symbol="BNBUSDT")
    solusdt = get_binance_data(symbol="SOLUSDT")
    ethusdt = get_binance_data(symbol="ETHUSDT")
    usd = get_binance_data(symbol="BUSDPLN")

    client = Client(API_KEY, API_SECRET)
    binance_balance = get_binance_balance(client)
    eth = 0
    for asset in binance_balance:
        item_amount = asset['total']  # Pobieramy całkowitą ilość danego aktywa
        eth += item_amount
    sol_stacking = get_staking_balance(client)
    saldo_bnb = balance_bnb * bnbusdt
    saldo_sol = solusdt* sol_stacking
    saldo_eth = eth * ethusdt
    total_pln = (saldo_bnb + saldo_sol + saldo_eth) * usd
    print(f"Saldo bnb wynosi: {saldo_bnb:.2f} USD czyli {saldo_bnb*usd:.2f} PLN")
    print(f"Saldo sol wynosi: {saldo_sol:.2f} USD czyli {saldo_sol*usd:.2f} PLN")
    print(f"Saldo eth wynosi: {saldo_eth:.2f} USD czyli {saldo_eth*usd:.2f} PLN")
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    deposit = 3000

    save_to_csv(current_date, bnbusdt, usd, saldo_bnb, saldo_sol, saldo_eth, total_pln, deposit)
    print(f"Profit: {total_pln - deposit:.2f} PLN")
    plot_total_balance()

if __name__ == "__main__":
    main()