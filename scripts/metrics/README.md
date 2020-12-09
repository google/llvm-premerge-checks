# Metrics

To measure the impact and usefulness of the pre-merge checks, we want to collect
a set of metrics. This doc will summarize the metrics and tools. All of the data
shall be collected as time series, so that we can see changes over time.

* Impact - The metrics we ultimately want to improve
    * Percentage of [build-bot build](http://lab.llvm.org:8011/) on main 
      failing. (Buildbot_percentage_failing)
    * Time to fix a broken main build: Time between start of failing builds 
      until the build is fixed. (BuildBot_time_to_fix)
    * Percentage of Revisions on Phabricator where a broken build was fixed 
      afterwards. This would indicate that a bug was found and fixed during 
      the code review phase. (Premerge_fixes)
    * Number of reverts on main. This indicates that something was broken on
      main that slipped through the pre-merge tests or was submitted without
      any review. (Upstream_reverts)

* Users and behavior - Interesting to see and useful to adapt our approach.
    * Percentage of commits to main that went through Phabricator.
    * Number of participants in pre-merge tests.
    * Percentage of Revisions with pre-merge tests executed
    * Number of 30-day active committers on main and Phabricator.

* Builds - See how the infrastructure is doing.
    * Time between upload of diff until build results available.
    * Percentage of Revisions with successful/failed tests
    * Number of pre-merge builds/day.
    * Build queuing time.
    * Individual times for `cmake`, `ninja all`, `ninja check-all` per 
      OS/architecture.
    * Result storage size.
    * Percentage of builds failing.

# Requirements

* Must: 
    * Do not collect/store personal data.
* Should:
    * Minimize the amount of additional tools/scripts we need to maintain.
    * Collect all metrics in a central location for easy evaluation (e.g. 
      database, CSV files).
* Nice to have:
    * As the data is from an open source project and available anyway, give 
      public access to the metrics (numbers and charts). 
    * Send out alerts/notifications.
    * Show live data in charts.


# Data sources

This section will explain where we can get the data from.

* build bot statistics

# Solution

We need to find solutions for these parts:
* Collect the data (regularly).
* Store the time series somewhere.
* Create & display charts.

Some ideas for this:
* bunch of scripts:
    * Run a bunch of scripts manually to generate the metrics every now and 
      then. Phabricator already has a database and most entries there have 
      timestamps. So we could also reconstruct the history from that.
    * TODO: Figure out if we can collect the most important metrics this way. 
      This requires that we can reconstruct historic values from the current
      logs/git/database/... entries.
* Jenkins + CSV + Sheets:
    * collect data with jenkins
    * store numbers as CSV in this repo
    * Charts are created manually on Google Sheets
* do it yourself:
    * Collect data with Jenkins jobs
    * Store the data on Prometheus 
    * Visualize with Grafana 
    * host all tools ourselves
* Stackdriver on GCP:
    * TODO: figure out if we can get all the required data into Stackdriver
* Jupyter notebooks:
    * TODO: figure out how that works
