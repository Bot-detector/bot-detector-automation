import os
import mysql.connector

from collections import namedtuple
from dotenv import load_dotenv, find_dotenv
from typing import List, NamedTuple

load_dotenv(find_dotenv(), verbose=True)

config_players = {
  'user':       os.getenv('SERVER_LOGIN'),
  'password':   os.getenv('SERVER_PASSWORD'),
  'host':       os.getenv('SERVER_ADDRESS'),
  'database':   os.getenv('DATABASE'),
}


def execute_sql(sql: str, insert: bool = False, param: dict = None):
    conn = mysql.connector.connect(**config_players)
    mycursor = conn.cursor(buffered=True, dictionary=True)

    mycursor.execute(sql, param)

    if insert:
        conn.commit()
        mycursor.close()
        conn.close()
        return

    rows = mycursor.fetchall()
    Record = namedtuple('Record', rows[0].keys())
    records = [Record(*r.values()) for r in rows]

    mycursor.close()
    conn.close()
    return records


# Get the total number of banned players we know of, even if we don't count them in our tally.
def get_count_banned_players() -> int:

    sql = '''
    SELECT COUNT(*) as bans FROM Players WHERE possible_ban = 1 AND confirmed_ban = 0 AND (label_jagex = 2 or label_jagex = 3)
    '''

    result = execute_sql(sql=sql)

    return result[0].bans


# Accounts that were banned but the ML thought were Real_players. We don't add these to our total.
def get_count_banned_real_players() -> int:
    
    sql = '''
        SELECT
            COUNT(*) as real_bans
        FROM Players pls
        JOIN Predictions pred on pred.name = pls.name
        WHERE possible_ban = 1 
            AND confirmed_ban = 0
            AND (label_jagex = 2 or label_jagex = 3)
            AND pred.Prediction LIKE "Real_player"
    '''
    
    result = execute_sql(sql=sql)

    return result[0].real_bans



# Accounts that were banned but the ML thought were Real_players. We don't add these to our total.
def get_count_banned_no_data() -> int:
    
    sql = '''
        SELECT
            COUNT(*) as no_data_bans
        FROM Players
        WHERE possible_ban = 1 
            AND confirmed_ban = 0
            AND (label_jagex = 2 or label_jagex = 3)
            AND id NOT IN (
                SELECT
                    distinct(Player_id)
                FROM playerHiscoreDataLatest
            )
    '''
    
    result = execute_sql(sql=sql)

    return result[0].no_data_bans



# The ML model thought these were bots. Count these!
def get_banned_bots_names() -> List[str]:
    
    sql = '''
        SELECT
            pls.name as name
        FROM Players pls
        JOIN Predictions pred on pred.name = pls.name
        WHERE possible_ban = 1 
            AND confirmed_ban = 0
            AND (label_jagex = 2 or label_jagex = 3)
            #AND pred.Prediction NOT LIKE "Real_Player"
            #AND pred.Prediction NOT LIKE "stats_too_low"
            AND pred.Real_player < 50
    '''
    try:
        bot_records = execute_sql(sql=sql)

        return [record.name for record in bot_records]

    except IndexError:
        return []


def apply_bot_bans():
    sql = '''
    UPDATE Players pls
    JOIN Predictions pred on pred.name = pls.name
	    SET pls.confirmed_ban = 1
    WHERE 1 = 1
	    AND pls.id > 0
	    AND (pls.label_jagex = 2 OR pls.label_jagex = 3)
        AND pls.possible_ban = 1
        #AND pred.prediction NOT LIKE "Real_player"
        AND pred.Real_player < 50
    '''

    execute_sql(sql=sql, insert=True)