#!/usr/bin/env python3

import psycopg2
import os
import datetime
import requests
from typing import Optional, Dict, List
import json

PHABRICATOR_URL = "https://reviews.llvm.org/api/"
BUILDBOT_URL = "https://lab.llvm.org/buildbot/api/v2/"


def connect_to_db() -> psycopg2.extensions.connection:
    """Connect to the database, create tables as needed."""
    conn = psycopg2.connect(
        "host=127.0.0.1 sslmode=disable dbname=stats user={} password={}".format(
            os.environ["PGUSER"], os.environ["PGPASSWORD"]
        )
    )
    return conn


def create_tables(conn: psycopg2.extensions.connection):
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS buildbot_workers (
            timestamp timestamp NOT NULL, 
            worker_id integer NOT NULL, 
            data jsonb NOT NULL
            );"""
    )
    cur.execute(
        """CREATE INDEX IF NOT EXISTS buildbot_worker_ids 
        ON buildbot_workers 
        (worker_id);"""
    )
    cur.execute(
        """CREATE INDEX IF NOT EXISTS buildbot_worker_timestamp 
        ON buildbot_workers 
        (timestamp);"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS buildbot_builds (
            builder_id integer NOT NULL, 
            build_number integer NOT NULL, 
            build_data jsonb NOT NULL,
            step_data jsonb NOT NULL
            );"""
    )
    conn.commit()


def get_worker_status(
    worker_id: int, conn: psycopg2.extensions.connection
) -> Optional[Dict]:
    """Note: postgres returns a dict for a stored json object."""
    cur = conn.cursor()
    cur.execute(
        "SELECT data FROM buildbot_workers WHERE worker_id = %s ORDER BY timestamp DESC;",
        [worker_id],
    )
    row = cur.fetchone()
    if row is None:
        return None
    return row[0]


def set_worker_status(
    timestamp: datetime.datetime,
    worker_id: int,
    data: str,
    conn: psycopg2.extensions.connection,
):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO buildbot_workers (timestamp, worker_id, data) values (%s,%s,%s);",
        (timestamp, worker_id, data),
    )


def update_worker_status(conn: psycopg2.extensions.connection):
    print("Updating worker status...")
    response = requests.get(BUILDBOT_URL + "workers")
    timestamp = datetime.datetime.now()
    for worker in response.json()["workers"]:
        worker_id = worker["workerid"]
        data = json.dumps(worker)
        old_data = get_worker_status(worker_id, conn)
        # only update worker information if it has changed as this data is quite
        # static
        if old_data is None or worker != old_data:
            set_worker_status(timestamp, worker_id, data, conn)
    conn.commit()


def get_builders() -> List[int]:
    """get list of all builder ids."""
    # TODO(kuhnel): do we also want to store the builder information?
    #               Does it contain useful information?
    response = requests.get(BUILDBOT_URL + "builders")
    return [builder["builderid"] for builder in response.json()["builders"]]


def get_last_build(builder_id: int, conn) -> int:
    """Get the latest build number for a builder.

    This is used to only get new builds."""
    cur = conn.cursor()
    cur.execute(
        "SELECT MAX(build_number) FROM buildbot_builds WHERE builder_id = %s;",
        [builder_id],
    )
    row = cur.fetchone()
    if row is None or row[0] is None:
        return 0
    return row[0]


def add_build(builder: int, number: int, build: str, steps: str, conn):
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO buildbot_builds 
           (builder_id, build_number, build_data,step_data) 
           values (%s,%s,%s,%s);""",
        (
            builder,
            number,
            json.dumps(build, sort_keys=True),
            json.dumps(steps, sort_keys=True),
        ),
    )


def update_build_status(conn):
    print("Updating build results...")
    # import only builds we have not yet stores in the database
    for builder in get_builders():
        url = BUILDBOT_URL + "builders/{}/builds?number__gt={}".format(
            builder, get_last_build(builder, conn)
        )
        response = requests.get(url)
        print("   builder {}".format(builder))
        # process builds in increasing order so we can resume the import process
        # if anything goes wrong
        for build in sorted(response.json()["builds"], key=lambda b: b["number"]):
            number = build["number"]
            # only store completed builds. Otherwise we would have to update them
            # after they are completed.
            if not build["complete"]:
                continue
            steps = requests.get(
                BUILDBOT_URL + "builders/{}/builds/{}/steps".format(builder, number)
            ).json()
            add_build(builder, number, build, steps, conn)
            conn.commit()


def buildbot_monitoring():
    """Main function of monitoring the phabricator server."""
    conn = connect_to_db()
    create_tables(conn)
    # update_worker_status(conn)
    update_build_status(conn)
    print("Completed, exiting...")


if __name__ == "__main__":
    buildbot_monitoring()
