sql_get_count_banned_players = """
SELECT
COUNT(*) as bans
FROM Players
WHERE 1=1
    AND possible_ban = 1
    AND confirmed_ban = 0
    AND label_jagex = 2
"""

sql_get_count_banned_real_players = """
    SELECT
        COUNT(pl.id) as real_bans
    FROM Players pl
    JOIN prediction_latest pred on pred.player_id = pl.id
    WHERE 1=1
        AND pl.possible_ban = 1 
        AND pl.confirmed_ban = 0
        AND pl.label_jagex = 2
        AND pred.prediction = "Real_player"
"""

sql_get_count_banned_no_data = """
SELECT
    COUNT(pl.id) as no_data_bans
FROM Players pl
WHERE 1=1
    AND pl.possible_ban = 1 
    AND pl.confirmed_ban = 0
    AND pl.label_jagex = 2
    AND pl.id NOT IN (
        SELECT
            player_id
        FROM highscore_data_latest
    )
"""

sql_get_banned_bots_names = """
    SELECT
        pl.name as name,
        pr.prediction as prediction
    FROM Players pl
    JOIN prediction_latest pr on pr.player_id = pl.id
    WHERE 1=1
        and pl.possible_ban = 1 
        AND pl.confirmed_ban = 0
        AND pl.label_jagex = 2
        AND JSON_EXTRACT(pr.predictions , '$."Real_Player"') < .5
"""

sql_apply_bot_bans = """
UPDATE Players pl
JOIN prediction_latest pr on pr.player_id = pl.id
    SET pl.confirmed_ban = 1
WHERE 1 = 1
    AND pl.label_jagex = 2
    AND pl.possible_ban = 1
    AND JSON_EXTRACT(pr.predictions , '$."Real_Player"') < .5
"""
