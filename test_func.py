import requests
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()




def get_stock_prices(stocks):
    """Функция для получения курса акций"""
    prices = {}
    APIKEY = os.getenv("API_KEY_ALPHA")
    base_url = 'https://www.alphavantage.co/query'

    for stock in stocks:
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': stock,
            'interval': '5min',
            'apikey': APIKEY
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Проверка на ошибки HTTP

            data = response.json()
            if 'Time Series (5min)' in data:
                # Получаем последнюю запись
                latest_time = sorted(data['Time Series (5min)'].keys())[0]
                prices[stock] = data['Time Series (5min)'][latest_time]['4. close']  # Цена закрытия
            else:
                logging.error(f"Нет данных для {stock}. Ответ: {data}")

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP ошибка при получении цены для {stock}: {http_err}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Ошибка сети при получении цены для {stock}: {req_err}")
        except KeyError as key_err:
            logging.error(f"Ошибка доступа к данным для {stock}: {key_err}")
        except Exception as e:
            logging.error(f"Произошла ошибка при получении цены для {stock}: {e}")

    return prices


# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)  # Настройка уровня логирования
    stocks_to_check = ['AAPL', 'MSFT', 'IBM']  # Пример списка акций
    prices = get_stock_prices(stocks_to_check)
    print(prices)



