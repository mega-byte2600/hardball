-- Skill persistence from the lake's hitting lines (player x season grain).
-- YoY self-join: does last year's walk rate / OBP carry into this year?
WITH lines AS (
  SELECT player_id, season,
         CAST(json_extract_string(stat_json, '$.obp') AS DOUBLE) AS obp,
         CAST(json_extract(stat_json, '$.baseOnBalls') AS DOUBLE)
           / NULLIF(CAST(json_extract(stat_json, '$.plateAppearances') AS DOUBLE), 0) AS bb_rate,
         CAST(json_extract(stat_json, '$.plateAppearances') AS INT) AS pa
  FROM fact_stat_lines WHERE group_name = 'hitting'
)
SELECT a.season AS season_from, COUNT(*) AS pairs,
       ROUND(CORR(a.bb_rate, b.bb_rate), 3) AS bb_rate_yoy_r,
       ROUND(CORR(a.obp, b.obp), 3) AS obp_yoy_r
FROM lines a JOIN lines b
  ON a.player_id = b.player_id AND b.season = a.season + 1
WHERE a.pa >= 200 AND b.pa >= 200
GROUP BY a.season ORDER BY a.season;
