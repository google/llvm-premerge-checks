#!/usr/bin/env python3

import psycopg2
from phabricator import Phabricator
import os
from typing import Optional
import datetime


def phab_up() -> Optional[Phabricator]:
    """Try to connect to phabricator to see if the server is up.

    Returns None if server is down.
    """
    print("Checking Phabricator status...")
    try:
        phab = Phabricator()
        phab.update_interfaces()
        print("Phabricator is up...")
        return phab
    except exception:
        pass
        print("Phabricator is down...")
    return None


def log_phab_status(up: bool, conn: psycopg2.extensions.connection):
    """log the phabricator status to the database."""
    print("Writing Phabricator status to database...")

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO phab_status (timestamp, status) VALUES (%s,%s);",
        (datetime.datetime.now(), up),
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
        "CREATE TABLE IF NOT EXISTS phab_status (timestamp timestamp, status boolean);"
    )
    conn.commit()
    return conn


def phab_monitoring():
    """Main function of monitoring the phabricator server."""
    conn = connect_to_db()
    phab = phab_up()
    log_phab_status(phab is not None, conn)
    print("Completed, exiting...")


if __name__ == "__main__":
    phab_monitoring()
