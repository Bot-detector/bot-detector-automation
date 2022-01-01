TIPOFF_CONFIG = '''
                SELECT DISTINCT
                    pl.name,
                    UNIX_TIMESTAMP(rp.timestamp)*1000 as timestamp,
                    rid.region_name,
                    p.prediction,
                    p.Predicted_confidence,
                    phd.*,
                    rp.*
                FROM Players as pl
                INNER JOIN Predictions as p on (p.id = pl.id)
                INNER JOIN reportLatest as rp on (rp.reported_id = pl.id)
                INNER JOIN playerHiscoreDataLatest as phd on phd.Player_id = pl.id
                INNER JOIN regionIDNames as rid on rid.region_ID = rp.region_ID
                WHERE 1=1
                    and p.Predicted_confidence > 99
                    and pl.possible_ban = 0
                    and pl.confirmed_ban = 0
                    and p.prediction != 'Real_Player'
                    and p.prediction != 'Stats Too Low'
                    and rp.timestamp >= current_timestamp() - interval 1 day
                '''
