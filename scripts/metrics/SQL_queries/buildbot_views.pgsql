/* Aggregated build information from multiple tables

  also extracts additional columns from json data to make access easier. */

CREATE OR REPLACE VIEW buildbot_overview AS
SELECT
    buildbot_buildsets.data -> 'sourcestamps' -> 0 ->> 'revision' AS revision,
    buildbot_builds.build_id,
    buildbot_builds.builder_id,
    buildbot_builds.build_number,
    buildbot_builds.build_data ->>'state_string' AS result,
    format('https://lab.llvm.org/buildbot/#/builders/%s/builds/%s', buildbot_builds.builder_id, buildbot_builds.build_number) as link,
    to_timestamp(CAST(build_data ->> 'complete_at' as int))::date as completed_at,
    to_timestamp(CAST(build_data ->> 'started_at' as int))::date as started_at
  FROM buildbot_buildsets, buildbot_buildrequests, buildbot_builds
    WHERE buildbot_buildrequests.buildset_id = buildbot_buildsets.buildset_id AND
      CAST(buildbot_builds.build_data ->> 'buildrequestid' AS int) = buildbot_buildrequests.buildrequest_id;
  