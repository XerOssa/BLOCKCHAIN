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
    
    df1 = df1.dropna(subset=['Date'])
    plt.clf()
    plt.plot(df1['Date'], df1['Total'], marker='o', linestyle='-', color='b', label='Total Balance (PLN)')
    plt.plot(df1['Date'], df1['Deposit'], marker='o', linestyle='-', color='r', label='Deposit')
    plt.title('Total Balance Over Time', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Total Balance (PLN)', fontsize=12)
    data_size = len(df1)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    if data_size >= 10:
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    else:
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.gca().xaxis.set_minor_locator(mdates.AutoDateLocator())
    plt.grid(axis='y', color='0.90')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()


def save_to_csv(date, total, deposit):
    file_exists = os.path.exists('balance_data.csv')

    with open('balance_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)

        if not file_exists:
            header = ['Date', 'Total', 'Deposit']
            writer.writerow(header)

        row = [date,  total, deposit] 
        writer.writerow(row)



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
            item['asset'], item['amount']
    else:
        print(f"Error: {response.status_code} - {response.text}")
    return float(item['amount']) if "amount" in item else None




def main():
    client = Client(API_KEY, API_SECRET)
    binance_balance = get_binance_balance(client)
    balance_bnb = get_wallet_balance(WALLET_ADDRESS, API_KEY1)
    usd = get_binance_data(symbol="BUSDPLN")
    sol = get_binance_data(symbol="SOLUSDC")
    bnb = get_binance_data(symbol="BNBUSDC")
    total_usd = 0
    sol_stacking = get_staking_balance(client)
    saldo_sol = sol * sol_stacking
    saldo_bnb = bnb * balance_bnb
    asset_data = {}

    for asset in binance_balance:
        amount = asset['total']
        asset_symbol = f'{asset["asset"]}USDC'
        
        # Jeśli aktywo to USDC, użyj samego symbolu bez dodawania 'USDC'
        if asset['asset'] == 'USDC':
            asset_price = 1.0  # Zakładamy, że USDC jest zawsze w stosunku 1:1 do USD
            saldo_usd = amount * asset_price
        else:
            asset_price = get_binance_data(asset_symbol)
            saldo_usd = amount * asset_price if asset_price else 0

        if saldo_usd > 0:
            asset_data[asset['asset']] = saldo_usd
            print(f"Saldo {asset['asset']}: {saldo_usd:.2f} USD")
            total_usd += saldo_usd


    total_pln = (total_usd + saldo_sol + saldo_bnb) * usd
    deposit = 4850
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Saldo bnb: {saldo_bnb:.2f} USD")
    print(f"Saldo sol stacking: {saldo_sol:.2f} USD")
    save_to_csv(current_date, total_pln, deposit)
    print(f"Profit: {total_pln - deposit:.2f} PLN")
    plot_total_balance()


if __name__ == "__main__":
    main()


