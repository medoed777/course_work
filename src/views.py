from datetime import datetime
from utils import load_user_settings, get_expense_data, generate_response


def main(date_input):
    date = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
    start_date = date.replace(day=1)
    end_date = date

    expense_data = get_expense_data(start_date, end_date, '../data/operations.xlsx')

    user_settings = load_user_settings()

    report = generate_response(expense_data, user_settings)

    print(report)


if __name__ == "__main__":
    main("2021-05-20 12:00:00")