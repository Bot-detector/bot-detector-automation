import numpy as np
import pandas as pd
import seaborn as sns
import requests
import json
import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), verbose=True)

token = os.getenv('token')

def get_report_latest_data():
    r = requests.get(f'https://osrsbotdetector.com/dev/v1/report/latest/bulk?token={token}&region_id=12100')
    if r.status_code != 200:
        return {'ERROR':r.status_code}
    data = json.loads(r.text)
    df = pd.DataFrame(data)
    if len(df) == 0:
        return {'ERROR': 'Dataframe could not be constructed, possibly due to insufficent response.'}
    return df