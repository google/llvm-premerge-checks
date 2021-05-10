#!/usr/bin/env python3

import psycopg2
from phabricator import Phabricator
import os
from typing import Optional
import datetime
import requests

PHABRICATOR_URL = "https://reviews.llvm.org/api/"
BUILDBOT_URL = "https://lab.llvm.org/buildbot/api/v2/"


def phab_up() -> Optional[Phabricator]:
    """Try to connect to phabricator to see if the server is up.

    Returns None if server is down.
    """
    print("Checking Phabricator status...")
    try:
        phab = Phabricator(host=PHABRICATOR_URL)
        phab.update_interfaces()
        print("  Phabricator is up.")
        return phab
    except Exception:
        pass
        print("  Phabricator is down.")
    return None


def buildbot_up() -> bool:
    """Check if buildbot server is up"""
    print("Checking Buildbot status...")
    try:
        response = requests.get(BUILDBOT_URL + "buildrequests?limit=100")
        if "masters" in response.json():
            print("  Buildbot is up.")
            return True
    except Exception:
        pass
    print("  Buildbot is down.")
    return False


def log_server_status(phab: bool, buildbot: bool, conn: psycopg2.extensions.connection):
    """log the phabricator status to the database."""
    print("Writing Phabricator status to database...")

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO server_status (timestamp, phabricator, buildbot) VALUES (%s,%s,%s);",
        (datetime.datetime.now(), phab, buildbot),
    )
    conn.commit()


def connect_to_db() -> psycopg2.extensions.connection:
    """Connect to the database, create tables as needed."""
    conn = psycopg2.connect(
        "host=127.0.0.1 sslmode=disable dbname=stats user={} password={}".format(
            os.environ["PGUSER"], os.environ["PGPASSWORD"]
        )
    )
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS server_status (timestamp timestamp, phabricator boolean, buildbot boolean);"
    )
    conn.commit()
    return conn


def server_monitoring():
    """Main function of monitoring the servers."""
    conn = connect_to_db()
    phab = phab_up()
    buildbot = buildbot_up()
    log_server_status(phab is not None, buildbot, conn)
    print("Completed, exiting...")


if __name__ == "__main__":
    server_monitoring()
