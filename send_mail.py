import csv
import smtplib
import ssl
from dotenv import load_dotenv
import os

load_dotenv()

from_address = os.getenv('from_address')
password = os.getenv('password')


message = """Hello!"""

context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    server.login(from_address, password)
    server.sendmail(
        from_address,
        from_address,
        message,
    )