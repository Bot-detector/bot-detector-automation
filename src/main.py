import get_report
import send_mail
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    try:
        os.mkdir('Reports/')
    except FileExistsError:
        pass
    
    df = get_report.get_tipoff_data()
    
    today_ISO = date.today().isoformat()
    dataframe_length = len(df.index)
    
    if dataframe_length > 1:
        REPORT_NAME = f'BDP-{today_ISO}-{dataframe_length}'
        REPORT_FILE_NAME = REPORT_NAME + '.csv'
        
        df.to_csv(f'Reports\\{REPORT_FILE_NAME}')
        PATH_TO_CSV_FILE = f'Reports\\{REPORT_FILE_NAME}'
        
        MESSAGE_BODY = f'Bot Detector Plugin Report for {today_ISO}.'
        EMAIL_SUBJECT = f'{REPORT_NAME} | ' + os.getenv('JMOD_TAG')
        
        send_mail.send_tipoff(MESSAGE_BODY=MESSAGE_BODY, EMAIL_SUBJECT=EMAIL_SUBJECT, PATH_TO_CSV_FILE=PATH_TO_CSV_FILE, FILE_NAME=REPORT_FILE_NAME)