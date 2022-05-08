import os
from datetime import date, datetime
from typing import List

from dotenv import find_dotenv, load_dotenv
import tipoff.functions as functions
import logging

load_dotenv(find_dotenv(), verbose=True)

def tipoff_bots():
    
    logging.info("Crafting Tipoff")
    try:
        os.mkdir('Reports/')
    except FileExistsError:
        pass

    df = functions.get_tipoff_data()
    today_ISO = date.today().isoformat()
    dataframe_length = len(df.index)

    if dataframe_length > 1:
        REPORT_NAME = f'BDP-{today_ISO}-{dataframe_length}'
        REPORT_FILE_NAME = REPORT_NAME + '.csv'

        df.to_csv(f'Reports\\{REPORT_FILE_NAME}')
        PATH_TO_CSV_FILE = f'Reports\\{REPORT_FILE_NAME}'

        MESSAGE_BODY = f'Bot Detector Plugin Report for {today_ISO}.'
        EMAIL_SUBJECT = f'{REPORT_NAME} | ' + os.getenv('JMOD_TAG')

        functions.send_tipoff(MESSAGE_BODY=MESSAGE_BODY, EMAIL_SUBJECT=EMAIL_SUBJECT,
                                PATH_TO_CSV_FILE=PATH_TO_CSV_FILE, FILE_NAME=REPORT_FILE_NAME)
