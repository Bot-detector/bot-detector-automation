import banbroadcaster.functions


def broadcast_bans():
    total_pending_bans, real_player_bans, no_data_bans, banned_bot_names, banned_bot_predictions = banbroadcaster.functions.get_ban_counts()
    num_bots_banned = len(banned_bot_names)

    banbroadcaster.functions.broadcast_totals(
        total_bans=total_pending_bans,
        real_player_bans=real_player_bans,
        no_data_bans=no_data_bans,
        bot_bans=num_bots_banned
    )

    banbroadcaster.functions.broadcast_names(names_list=banned_bot_names)
    banbroadcaster.functions.apply_bot_bans()
    banbroadcaster.functions.broadcast_bans_complete(num_bans=num_bots_banned)
    banbroadcaster.functions.post_bans_tweet(num_bans=num_bots_banned)
    banbroadcaster.functions.post_breakdown_tweet(banned_bot_predictions)
