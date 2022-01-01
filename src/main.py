import os
import time
from datetime import date, datetime
from typing import List

import tweepy
from discord_webhook import DiscordWebhook
from discord_webhook.webhook import DiscordEmbed
from dotenv import find_dotenv, load_dotenv

import sql
import tipoff.get_report as get_report
import tipoff.send_mail as send_mail

load_dotenv(find_dotenv(), verbose=True)

GRAVEYARD_WEBHOOK_URL = os.environ.get('GRAVEYARD_WEBHOOK')

AUTH = tweepy.OAuthHandler(consumer_key=os.environ.get('consumer_key'), consumer_secret=os.environ.get('consumer_secret'))
AUTH.set_access_token(key=os.environ.get('access_token'), secret=os.environ.get('access_token_secret'))

TWITTER_API = tweepy.API(AUTH, wait_on_rate_limit=True)

def broadcast_totals(total_bans:int, real_player_bans: int, no_data_bans: int, bot_bans: int):
    embed = DiscordEmbed(title="Pending Bans Stats", color="000000", description=f"Latest Ban Totals From Our Hiscores Scrapes")
    embed.set_timestamp()
    embed.add_embed_field(name="Total Unapplied Bans", value=f"{total_bans:,}", inline=False)
    embed.add_embed_field(name="Predicted as Real Player (Not Counted)", value=f"{real_player_bans:,}", inline=False)
    embed.add_embed_field(name="No Hiscore Data (Not Counted)", value=f"{no_data_bans:,}", inline=False)
    embed.add_embed_field(name="Predicted as Bots (These Count)", value=f"{bot_bans:,}", inline=False)
    embed.set_thumbnail(url="https://c.tenor.com/V71SmWqyYHkAAAAM/kermit-freaking.gif")

    webhook = DiscordWebhook(url=GRAVEYARD_WEBHOOK_URL, rate_limit_retry=True)
    webhook.add_embed(embed=embed)
    webhook.execute()


def broadcast_names(names_list: List[str]):
    while True:
        num_pending_players = len(names_list)
        # if is empty list break
        if not names_list:
            break
        elif num_pending_players > 50:
            broadcast_size = 50
        else:
            broadcast_size = num_pending_players
        players_to_broadcast = []

        for i in range(broadcast_size):
            players_to_broadcast.append(names_list.pop())

        embed = DiscordEmbed(title="All Ye Bots Lose All Hope!", color="000000", description=f"{broadcast_size} Accounts")
        embed.set_timestamp()
        embed.add_embed_field(name="Bans Being Added", value=f"{', '.join(players_to_broadcast)}")
        embed.set_thumbnail(url="https://i.imgur.com/PPnZRHW.gif")

        webhook = DiscordWebhook(url=GRAVEYARD_WEBHOOK_URL)
        webhook.add_embed(embed=embed)

        try:
            webhook.execute()
        except Exception as e:
            #logger.error(f"Discord Webhook Error: {e}")
            pass

        time.sleep(5)


def post_bans_tweet(num_bans: int):

    msg = f"BANS ALERT - {datetime.now().strftime('%d-%m-%Y')}: {num_bans:,d} accounts our system has detected as bots have been banned in the last 24 hours."
    TWITTER_API.update_status(msg)

    
def broadcast_bans_complete(num_bans: int):
    if num_bans > 0:
        embed = DiscordEmbed(title="Bans Added!", color="000000", description=f"Bans were added to the project's total. Time to check your kc! ")
        embed.set_timestamp()
        embed.add_embed_field(name="Total Bans Added:", value=f"{num_bans:,}", inline=False)
        embed.set_thumbnail(url="https://oldschool.runescape.wiki/images/5/58/Crazy_dance.gif")
        webhook = DiscordWebhook(url=GRAVEYARD_WEBHOOK_URL, rate_limit_retry=True)
        webhook.add_embed(embed=embed)
        webhook.execute()

        webhook = DiscordWebhook(url=GRAVEYARD_WEBHOOK_URL, rate_limit_retry=True, content='<@&893399220172767253>')
        webhook.execute()

if __name__ == '__main__':
    total_pending_bans = sql.get_count_banned_players()
    real_player_bans = sql.get_count_banned_real_players()
    no_data_bans = sql.get_count_banned_no_data()
    banned_bot_names = sql.get_banned_bots_names()

    num_bots_banned = len(banned_bot_names)

    broadcast_totals(
        total_bans=total_pending_bans,
        real_player_bans=real_player_bans,
        no_data_bans=no_data_bans,
        bot_bans=num_bots_banned
    )

    broadcast_names(names_list=banned_bot_names)

    sql.apply_bot_bans()

    broadcast_bans_complete(num_bans=num_bots_banned)
    post_bans_tweet(num_bans=num_bots_banned)
    
    
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
