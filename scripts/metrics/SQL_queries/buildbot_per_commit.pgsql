/* list last 100 git commits with number of builds and success rate */
SELECT git_commits.hash as revision,
  count(*) as num_builds,
  (100.0*count(CASE WHEN buildbot_overview.result='build successful' THEN 1 END)/count(*)) as success_prct
FROM buildbot_overview, git_commits 
WHERE buildbot_overview.revision = git_commits.hash
GROUP BY git_commits.hash 
ORDER BY git_commits.commit_time DesC
LIMIT 100