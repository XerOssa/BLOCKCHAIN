import requests
import matplotlib.pyplot as plt
from datetime import datetime




# Pobieranie aktualnej ceny BNB z Binance
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

# Rysowanie wykresu salda w czasie
def plot_balance(timestamps, balances):
    plt.clf()
    plt.plot(timestamps, balances, marker='o', linestyle='-', color='b')
    plt.title('BNB Balance Over Time', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('BNB Balance', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Główna funkcja
def main():
    wallet_address = "0xff494b777A795B6Eed2fc245acee43F4dD3B456E"
    api_key = "VC142F8ZFU9TX5FFMHUY1S1W3RATWF89AV"
    
    balance_bnb = get_wallet_balance(wallet_address, api_key)
    
    bnbusdt = get_binance_data(symbol="BNBUSDT")
    usd = get_binance_data(symbol="BUSDPLN")
   
    saldo = balance_bnb * bnbusdt
    total = saldo * usd
    print(f"Saldo portfela wynosi:  {saldo:.2f} USD czyli {total:.2f} PLN")
    
    # Aktualizacja danych do wykresu
    current_date = datetime.now().strftime('%Y-%m-%d')
    timestamps = [current_date]  # Możesz rozszerzyć listę dla historii
    balances = [balance_bnb]
    
    plot_balance(timestamps, balances)

# Uruchomienie programu
if __name__ == "__main__":
    main()
