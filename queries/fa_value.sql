-- Top of the 2027 FA class by projected WAR per $10M of prior AAV
-- (prior AAV = last-price anchor, not a predicted 2027 salary).
SELECT name, pos, prev_team,
       ROUND(steamer_war, 2) AS steamer_war,
       ROUND(prev_aav / 1e6, 1) AS prior_aav_m,
       ROUND(war_per_10m_prior_aav, 2) AS war_per_10m
FROM fact_fa_class
WHERE steamer_war IS NOT NULL AND prev_aav > 0
ORDER BY war_per_10m DESC LIMIT 15;
