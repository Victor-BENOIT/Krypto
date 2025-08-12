
from binance.client import Client


api_key ="VJgxP21FizEKnMFFejKXjVQWnBq5IJr07TfzhTTdraJbZf9D5TIbr9ZYhEvh5tbq"
api_secret="Y35zrGsNKvG6XErZ2pKIOcJIjyaowOzXG2h1fdXqYydhGEqOczgvRUsKRwg3p1L8"

client_binance = Client(api_key, api_secret)
account_info = client_binance.get_account()
balances = account_info.get("balances", [])

print("Balances:")
for balance in balances:
    asset = balance["asset"]
    free = float(balance["free"])
    locked = float(balance["locked"])
    if free > 0 or locked > 0:
        print(f"{asset}: Free: {free}, Locked: {locked}")