import pandas as pd
from dotenv import load_dotenv
import os
import pymysql

load_dotenv()

TIPOFF_CONFIG = '''
                SELECT DISTINCT
                    pl.name,
                    UNIX_TIMESTAMP(rp.timestamp)*1000 as timestamp,
                    rid.region_name,
                    p.prediction,
                    p.Predicted_confidence,
                    phd.*,
                    rp.*
                FROM Players as pl
                INNER JOIN Predictions as p on (p.id = pl.id)
                INNER JOIN reportLatest as rp on (rp.reported_id = pl.id)
                INNER JOIN playerHiscoreDataLatest as phd on phd.Player_id = pl.id
                INNER JOIN regionIDNames as rid on rid.region_ID = rp.region_ID
                WHERE 1=1
                    and p.Predicted_confidence > 99
                    and pl.possible_ban = 0
                    and pl.confirmed_ban = 0
                    and p.prediction != 'Real_Player'
                    and p.prediction != 'Stats Too Low'
                    and rp.timestamp >= current_timestamp() - interval 1 day
                '''

def get_tipoff_data():
    connection = pymysql.connect(
                                host=os.getenv('SERVER_ADDRESS'),
                                user=os.getenv('SERVER_LOGIN'),
                                passwd=os.getenv('SERVER_PASSWORD'),
                                database=os.getenv('DATABASE')
                                )
    cursor = connection.cursor()
    cursor.execute(TIPOFF_CONFIG)
    df = pd.DataFrame([tuple(row) for row in cursor.fetchall()], columns = [desc[0] for desc in cursor.description])
    connection.commit()
    connection.close()
    return df