load_dotenv()

APIKEY = os.getenv("API_KEY")

headers = {"apikey": f"{APIKEY}"}


def conversion_currency(transactions: dict) -> Any:
    """Конвертирует валюту из USD и EUR в рубли и возвращает сумму"""
    amount = transactions.get("amount")
    currency = transactions.get("currency")

    if currency == "RUB":
        return amount

    try:
        response = requests.get(
            f"https://api.apilayer.com/exchangerates_data/convert?to=RUB&from={currency}&amount={amount}",
            headers=headers,
        )

        response.raise_for_status()

        data = response.json()

        if "result" in data:
            return data["result"]
        else:
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

    return None