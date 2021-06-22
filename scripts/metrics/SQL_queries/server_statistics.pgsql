
/* get server uptime statistics in percent */
SELECT DATE(timestamp) as date,
  count(*) as measurements,
  (100.0*count(CASE WHEN phabricator THEN 1 END)/count(*)) as phabricator_up_prcnt,
  (100.0*count(CASE WHEN buildbot THEN 1 END)/count(*)) as buildbot_up_prcnt
  FROM server_status GROUP BY date ORDER BY date ASC;