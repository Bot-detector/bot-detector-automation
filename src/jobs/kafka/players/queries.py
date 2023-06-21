sql = """
select * from (
    SELECT 
        pl.id AS id,
        pl.name AS name,
        pl.created_at AS created_at,
        pl.updated_at AS updated_at,
        pl.possible_ban AS possible_ban,
        pl.confirmed_ban AS confirmed_ban,
        pl.confirmed_player AS confirmed_player,
        pl.label_id AS label_id,
        pl.label_jagex AS label_jagex
    FROM(
        SELECT 
            pl.id AS id,
            pl.name AS name,
            pl.created_at AS created_at,
            pl.updated_at AS updated_at,
            pl.possible_ban AS possible_ban,
            pl.confirmed_ban AS confirmed_ban,
            pl.confirmed_player AS confirmed_player,
            pl.label_id AS label_id,
            pl.label_jagex AS label_jagex,
            rpl.created_at AS last_seen,
            (CASE
                WHEN (pl.updated_at IS NULL) THEN 0
                WHEN (pl.confirmed_player = 1) THEN 1
                WHEN ( 1=1
                    AND (pl.possible_ban = 1)
                    AND (pl.confirmed_ban = 0)
                ) THEN 98
                WHEN (pl.confirmed_ban = 1) THEN 99
                WHEN (pl.label_jagex <> 0) THEN 100
                ELSE 2
            END) AS scrape_priority
        FROM Players pl
        LEFT JOIN reportLatest rpl ON (pl.id = rpl.reported_id)
        where 1=1
            and LENGTH(pl.name) <= 12
    ) pl
    ORDER BY pl.scrape_priority
) a
"""