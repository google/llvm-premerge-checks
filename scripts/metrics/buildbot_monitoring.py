#!/usr/bin/env python3

import psycopg2
import os
import datetime
import requests
from typing import Optional, Dict
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


def buildbot_monitoring():
    """Main function of monitoring the phabricator server."""
    conn = connect_to_db()
    create_tables(conn)
    update_worker_status(conn)
    print("Completed, exiting...")


if __name__ == "__main__":
    buildbot_monitoring()
