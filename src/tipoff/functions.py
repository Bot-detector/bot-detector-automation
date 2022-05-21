import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import pymysql
import src.config as config

from src.tipoff.queries import *

logger = logging.getLogger(__name__)


def get_tipoff_data():
    logger.info("Getting tipoff information")
    connection = pymysql.connect(
        host=config.SERVER_ADDRESS,
        user=config.SERVER_LOGIN,
        passwd=config.SERVER_PASSWORD,
        database=config.DATABASE,
    )
    cursor = connection.cursor()
    cursor.execute(TIPOFF_CONFIG)
    df = pd.DataFrame(
        [tuple(row) for row in cursor.fetchall()],
        columns=[desc[0] for desc in cursor.description],
    )
    connection.commit()
    connection.close()
    return df


def send_tipoff(MESSAGE_BODY, EMAIL_SUBJECT, PATH_TO_CSV_FILE, FILE_NAME):
    logger.info("Sending Tipoff")
    msg = MIMEMultipart()
    body_part = MIMEText(MESSAGE_BODY, "plain")

    msg["Subject"] = EMAIL_SUBJECT
    msg["From"] = config.EMAIL_FROM
    msg["To"] = config.EMAIL_TIPOFF

    msg.attach(body_part)
    with open(PATH_TO_CSV_FILE, "rb") as file:
        msg.attach(MIMEApplication(file.read(), Name=FILE_NAME))
    smtp_obj = smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT)
    smtp_obj.login(config.EMAIL_FROM, config.SMTP_PASSWORD)
    smtp_obj.sendmail(msg["From"], msg["To"], msg.as_string())
    smtp_obj.quit()
