/* list builders with success rate <70% over the last 7 days
   
   these are probably worth investigating
 */
 
Select *,
format('https://lab.llvm.org/buildbot/#/builders/%s', builder_id) as link
 FROM (
  SELECT 
    builder_id,
    count(*) as num_builds,
    (100.0*count(CASE WHEN buildbot_overview.result='build successful' THEN 1 END)/count(*)) as success_prct
  FROM buildbot_overview
  WHERE completed_at > current_date - interval '7' day
  GROUP BY builder_id
) as builder_success
WHERE success_prct < 70