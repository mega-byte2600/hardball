-- Who the proposed 2027 cap/floor forces to act (fact_cap_scenario).
SELECT team,
       ROUND(payroll_M, 1) AS payroll_m,
       CASE WHEN gap_to_cap > 0 THEN 'OVER CAP - must shed'
            WHEN gap_to_floor > 0 THEN 'UNDER FLOOR - must add'
            ELSE 'compliant' END AS status,
       ROUND(GREATEST(gap_to_cap, gap_to_floor) / 1e6, 1) AS action_m
FROM fact_cap_scenario
WHERE gap_to_cap > 0 OR gap_to_floor > 0
ORDER BY action_m DESC;
