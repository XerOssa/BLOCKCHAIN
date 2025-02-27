import os
import requests
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import matplotlib.dates as mdates
from dotenv import load_dotenv


load_dotenv()

WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
API_KEY = os.getenv("API_KEY")


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
    df = pd.read_csv('balance_data.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    plt.clf()
    plt.plot(df['Date'], df['Total'], marker='o', linestyle='-', color='b', label='Total Balance (PLN)')
    plt.plot(df['Date'], df['Deposit'], marker='o', linestyle='-', color='r', label='Deposit')
    plt.title('Total Balance Over Time', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Total Balance (PLN)', fontsize=12)
    data_size = len(df)
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


def save_to_csv(date, bnbusdt, usd, saldo, total, deposit):
    file_exists = False
    try:
        with open('balance_data.csv', 'r'):
            file_exists = True
    except FileNotFoundError:
        pass
    with open('balance_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            writer.writerow(['Date', 'BNB/USDT', 'USD/PLN', 'Saldo', 'Total', 'Deposit'])
        
        writer.writerow([date, bnbusdt, usd, saldo, total, deposit])


def main():
    balance_bnb = get_wallet_balance(WALLET_ADDRESS, API_KEY)
    bnbusdt = get_binance_data(symbol="BNBUSDT")
    usd = get_binance_data(symbol="BUSDPLN")
    saldo = balance_bnb * bnbusdt
    total = saldo * usd
    print(f"Saldo portfela wynosi:  {saldo:.2f} USD czyli {total:.2f} PLN")
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    deposit = 1000
    save_to_csv(current_date, bnbusdt, usd, saldo, total, deposit)
    print(f"Profit: {total - deposit:.2f} PLN")
    plot_total_balance()


if __name__ == "__main__":
    main()
