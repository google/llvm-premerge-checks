/* list number of builds and percentage of successful builds per day */
SELECT to_date(cast(git_commits.commit_time as TEXT),'YYYY-MM-DD')  as date,
  count(*) as num_builds,
  (100.0*count(CASE WHEN buildbot_overview.result='build successful' THEN 1 END)/count(*)) as success_prct
FROM buildbot_overview, git_commits 
WHERE buildbot_overview.revision = git_commits.hash
GROUP BY date ORDER BY date ASC;