def main(date_input):
    date = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
    start_date = date.replace(day=1)
    end_date = date

    expense_data = get_expense_data(start_date, end_date)

    user_settings = load_user_settings()

    report = generate_response(expense_data, user_settings)

    print(report)


if __name__ == "__main__":
    main("2020-05-20 12:00:00")