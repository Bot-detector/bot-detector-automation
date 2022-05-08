import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import pymysql
from dotenv import load_dotenv
import logging

from tipoff.queries import *

load_dotenv()

def get_tipoff_data():
    logging.info('Getting tipoff information')
    connection = pymysql.connect(
        host=os.getenv('SERVER_ADDRESS'),
        user=os.getenv('SERVER_LOGIN'),
        passwd=os.getenv('SERVER_PASSWORD'),
        database=os.getenv('DATABASE')
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
    msg['From'] = os.getenv('EMAIL_FROM')
    msg['To'] = os.getenv('EMAIL_TIPOFF')

    msg.attach(body_part)
    with open(PATH_TO_CSV_FILE, 'rb') as file:
        msg.attach(MIMEApplication(file.read(), Name=FILE_NAME))
    smtp_obj = smtplib.SMTP_SSL(
        os.getenv('SMTP_SERVER'), os.getenv('SMTP_PORT'))
    smtp_obj.login(os.getenv('EMAIL_FROM'), os.getenv('SMTP_PASSWORD'))
    smtp_obj.sendmail(msg['From'], msg['To'], msg.as_string())
    smtp_obj.quit()
