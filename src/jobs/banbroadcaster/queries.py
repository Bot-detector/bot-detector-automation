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
        COUNT(*) as real_bans
    FROM Players pls
    JOIN Predictions pred on pred.name = pls.name
    WHERE possible_ban = 1 
        AND confirmed_ban = 0
        AND label_jagex = 2
        AND pred.Prediction LIKE "Real_player"
"""

sql_get_count_banned_no_data = """
SELECT
    COUNT(*) as no_data_bans
FROM Players
WHERE 1=1
    AND possible_ban = 1 
    AND confirmed_ban = 0
    AND label_jagex = 2
    AND id NOT IN (
        SELECT
            Player_id
        FROM playerHiscoreDataLatest
    )
"""

sql_get_banned_bots_names = """
    SELECT
        pl.name as name,
        pr.Prediction as prediction
    FROM Players pl
    JOIN Predictions pr on pred.id = pls.id
    WHERE 1=1
        and pl.possible_ban = 1 
        AND pl.confirmed_ban = 0
        AND pl.label_jagex = 2
        AND pr.Real_player < 50
"""

sql_apply_bot_bans = """
UPDATE Players pl
JOIN Predictions pr on pr.id = pl.id
    SET pl.confirmed_ban = 1
WHERE 1 = 1
    AND pl.label_jagex = 2
    AND pl.possible_ban = 1
    AND pr.Real_player < 50
"""
