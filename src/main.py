from apscheduler.schedulers.background import BackgroundScheduler

import tipoff.main_tipoff
import banbroadcaster.main_broadcaster

scheduler = BackgroundScheduler()

if __name__ == '__main__':
    #Broadcast bans to #bot-graveyard on Discord, send total bans tweet, and send bans breakdowns tweets
    scheduler.add_job(banbroadcaster.main_broadcaster.broadcast_bans, 'cron', hour=20, minute=5, misfire_grace_time=60)

    #Send next tipoff batch to Jagex
    scheduler.add_job(tipoff.main_tipoff.tipoff_bots, 'cron', hour=20, minute=45, misfire_grace_time=60)

    scheduler.start()
