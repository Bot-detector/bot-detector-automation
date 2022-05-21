import src.banbroadcaster.functions as banfunctions


def broadcast_bans(Twitter=True, Discord=True):
    """
    Posts bans to twitter and discord.
    """
    (
        total_pending_bans,
        real_player_bans,
        no_data_bans,
        banned_bot_names,
        banned_bot_predictions,
    ) = banfunctions.get_ban_counts()
    num_bots_banned = len(banned_bot_names)

    if Discord:
        banfunctions.broadcast_totals(
            total_bans=total_pending_bans,
            real_player_bans=real_player_bans,
            no_data_bans=no_data_bans,
            bot_bans=num_bots_banned,
        )
        banfunctions.broadcast_names(names_list=banned_bot_names)
        banfunctions.apply_bot_bans()
        banfunctions.broadcast_bans_complete(num_bans=num_bots_banned)

    if Twitter:
        banfunctions.post_bans_tweet(num_bans=num_bots_banned)
        banfunctions.post_breakdown_tweets(banned_bot_predictions)
