import logging

from . import functions

logger = logging.getLogger(__name__)


def broadcast_bans():
    logger.debug("get_ban_counts")
    (
        total_pending_bans,
        real_player_bans,
        no_data_bans,
        banned_bot_names,
        banned_bot_predictions,
    ) = functions.get_ban_counts()

    num_bots_banned = len(banned_bot_names)

    logger.debug("apply_bot_bans")
    functions.apply_bot_bans()

    logger.debug("broadcast_totals")
    functions.broadcast_totals(
        total_bans=total_pending_bans,
        real_player_bans=real_player_bans,
        no_data_bans=no_data_bans,
        bot_bans=num_bots_banned,
    )

    logger.debug("broadcast_names")
    functions.broadcast_names(names_list=banned_bot_names)
    logger.debug("broadcast_bans_complete")
    functions.broadcast_bans_complete(num_bans=num_bots_banned)
    # logger.debug("post_bans_tweet")
    # functions.post_bans_tweet(num_bans=num_bots_banned)
    # logger.debug("post_breakdown_tweets")
    # functions.post_breakdown_tweets(banned_bot_predictions)


if __name__ == "__main__":
    broadcast_bans()
