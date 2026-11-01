-- PARITY: recompute the Marcel-vs-Steamer benchmark from curated tables.
-- The committed artifact (Cycle 22) reports OBP r = 0.889 on 201 matched
-- hitters; this query must reproduce it from the warehouse alone.
SELECT COUNT(*) AS matched,
       ROUND(CORR(p.proj_OBP, s.OBP), 3) AS obp_pearson_r,
       ROUND(AVG(ABS(p.proj_OBP - s.OBP)), 4) AS mean_abs_diff
FROM fact_proj_hitters p
JOIN fact_steamer_bat s ON s.xMLBAMID = p.player_id;
