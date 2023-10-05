sql_get_count_banned_players = """
SELECT
COUNT(*) as bans
FROM Players
WHERE (possible_ban = 1
AND confirmed_ban = 0
AND (label_jagex = 2 or label_jagex = 3))
"""

sql_get_count_banned_real_players = """
    SELECT
        COUNT(*) as real_bans
    FROM Players pls
    JOIN Predictions pred on pred.name = pls.name
    WHERE possible_ban = 1 
        AND confirmed_ban = 0
        AND (label_jagex = 2 or label_jagex = 3)
        AND pred.Prediction LIKE "Real_player"
"""

sql_get_count_banned_no_data = """
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
"""

sql_get_banned_bots_names = """
    SELECT
        pls.name as name,
        pred.Prediction as prediction
    FROM Players pls
    JOIN Predictions pred on pred.name = pls.name
    WHERE possible_ban = 1 
        AND confirmed_ban = 0
        AND (label_jagex = 2 or label_jagex = 3)
        #AND pred.Prediction NOT LIKE "Real_Player"
        #AND pred.Prediction NOT LIKE "stats_too_low"
        AND pred.Real_player < 50
"""

sql_apply_bot_bans = """
UPDATE Players pls
JOIN Predictions pred on pred.name = pls.name
    SET pls.confirmed_ban = 1
WHERE 1 = 1
    AND pls.id > 0
    AND (pls.label_jagex = 2 OR pls.label_jagex = 3)
    AND pls.possible_ban = 1
    #AND pred.prediction NOT LIKE "Real_player"
    AND pred.Real_player < 50
"""
