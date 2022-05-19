import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import pymysql
from config import (DATABASE, EMAIL_FROM, EMAIL_TIPOFF, SERVER_ADDRESS,
                    SERVER_LOGIN, SERVER_PASSWORD, SMTP_PASSWORD, SMTP_PORT,
                    SMTP_SERVER)
from dotenv import load_dotenv

from tipoff.queries import *

load_dotenv()

def get_tipoff_data():
    logging.info('Getting tipoff information')
    connection = pymysql.connect(
        host=SERVER_ADDRESS,
        user=SERVER_LOGIN,
        passwd=SERVER_PASSWORD,
        database=DATABASE
    )
    cursor = connection.cursor()
    cursor.execute(TIPOFF_CONFIG)
    df = pd.DataFrame([tuple(row) for row in cursor.fetchall()], columns=[
                      desc[0] for desc in cursor.description])
    connection.commit()
    connection.close()
    return df


def send_tipoff(MESSAGE_BODY, EMAIL_SUBJECT, PATH_TO_CSV_FILE, FILE_NAME):
    logging.info('Sending Tipoff')
    msg = MIMEMultipart()
    body_part = MIMEText(MESSAGE_BODY, 'plain')

    msg['Subject'] = EMAIL_SUBJECT
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TIPOFF

    msg.attach(body_part)
    with open(PATH_TO_CSV_FILE, 'rb') as file:
        msg.attach(MIMEApplication(file.read(), Name=FILE_NAME))
    smtp_obj = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    smtp_obj.login(EMAIL_FROM, SMTP_PASSWORD)
    smtp_obj.sendmail(msg['From'], msg['To'], msg.as_string())
    smtp_obj.quit()
