from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv
import os

load_dotenv()

def send_tipoff(MESSAGE_BODY, EMAIL_SUBJECT, PATH_TO_CSV_FILE, FILE_NAME):
    msg = MIMEMultipart()
    body_part = MIMEText(MESSAGE_BODY, 'plain')
    
    msg['Subject'] = EMAIL_SUBJECT
    msg['From'] = os.getenv('EMAIL_FROM')
    msg['To'] = os.getenv('EMAIL_TIPOFF')
    
    msg.attach(body_part)
    with open(PATH_TO_CSV_FILE,'rb') as file:
        msg.attach(MIMEApplication(file.read(), Name=FILE_NAME))
    smtp_obj = smtplib.SMTP_SSL(os.getenv('SMTP_SERVER'), os.getenv('SMTP_PORT'))
    smtp_obj.login(os.getenv('EMAIL_FROM'), os.getenv('SMTP_PASSWORD'))
    smtp_obj.sendmail(msg['From'], msg['To'], msg.as_string())
    smtp_obj.quit()