import requests
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import matplotlib.dates as mdates

# Pobieranie ceny z Binance
def get_binance_data(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    return float(data["price"]) if "price" in data else None

# Pobieranie salda portfela z BscScan
def get_wallet_balance(wallet_address, api_key):
    url = f"https://api.bscscan.com/api?module=account&action=balance&address={wallet_address}&tag=latest&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if data["status"] == "1":
        balance_wei = int(data["result"])
        return balance_wei / 10**18  # Konwersja z Wei na BNB
    else:
        print(f"Błąd: {data['message']}")
        return None

# Rysowanie wykresu total w czasie
def plot_total_balance():
    # Wczytywanie danych z pliku CSV
    df = pd.read_csv('balance_data.csv')

    # Konwertowanie kolumny 'Date' na format datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Tworzenie wykresu
    plt.clf()
    plt.plot(df['Date'], df['Total'], marker='o', linestyle='-', color='b', label='Total Balance (PLN)')
    plt.plot(df['Date'], df['Deposit'], marker='o', linestyle='-', color='r', label='Deposit')
    plt.title('Total Balance Over Time', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Total Balance (PLN)', fontsize=12)

    # Liczba punktów danych
    data_size = len(df)

    # Ustawienie formatu daty na osi X
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    # Dynamiczne ustawienie interwału na osi X w zależności od liczby punktów
    if data_size <= 10:  # Dla małej liczby danych (np. do 10 punktów)
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))  # Co godzinę
    elif data_size <= 30:  # Dla danych do 30 punktów
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Co dzień
    else:  # Dla dużej liczby danych (ponad 30 punktów)
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))  # Co miesiąc

    # Automatyczne dopasowanie etykiet na osi X
    plt.gca().xaxis.set_minor_locator(mdates.AutoDateLocator())

    # Rotacja etykiet
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()

# Funkcja do zapisywania danych do CSV
def save_to_csv(date, bnbusdt, usd, saldo, total, deposit):
    # Sprawdzamy, czy plik już istnieje, jeśli nie, to zapisujemy nagłówki
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

# Główna funkcja
def main():
    wallet_address = "0xff494b777A795B6Eed2fc245acee43F4dD3B456E"
    api_key = "VC142F8ZFU9TX5FFMHUY1S1W3RATWF89AV"
    
    # Pobieranie danych
    balance_bnb = get_wallet_balance(wallet_address, api_key)
    bnbusdt = get_binance_data(symbol="BNBUSDT")
    usd = get_binance_data(symbol="BUSDPLN")
   
    saldo = balance_bnb * bnbusdt
    total = saldo * usd
    
    print(f"Saldo portfela wynosi:  {saldo:.2f} USD czyli {total:.2f} PLN")
    
    # Zapisywanie danych do CSV
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Zmieniony format na godzinę i minutę
    deposit = 1000
    save_to_csv(current_date, bnbusdt, usd, saldo, total, deposit)
    

    print(f"Profit: {total - deposit:.2f} PLN")
    
    # Tworzenie wykresu
    plot_total_balance()

# Uruchomienie programu
if __name__ == "__main__":
    main()
