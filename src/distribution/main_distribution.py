import functions

if __name__ == '__main__':
    data = functions.get_report_latest_data()
    if type(data) != dict:
        df = data
        print(df)
    else:
        print(data['ERROR'])
    