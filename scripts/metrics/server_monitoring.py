#!/usr/bin/env python3
import traceback
import psycopg2
from phabricator import Phabricator
import os
from typing import Optional
import datetime
import requests
import logging

PHABRICATOR_URL = "https://reviews.llvm.org/api/"
BUILDBOT_URL = "https://lab.llvm.org/buildbot/api/v2"


def phab_up() -> Optional[Phabricator]:
    """Try to connect to phabricator to see if the server is up.

    Returns None if server is down.
    """
    logging.info("Checking Phabricator status...")
    try:
        phab = Phabricator(token=os.getenv('CONDUIT_TOKEN'), host=PHABRICATOR_URL)
        phab.update_interfaces()
        logging.info("Phabricator is up.")
        return phab
    except Exception as ex:
        logging.error(ex)
        logging.error(traceback.format_exc())
        logging.warning("Phabricator is down.")
    return None


def buildbot_up() -> bool:
    """Check if buildbot server is up"""
    logging.info("Checking Buildbot status...")
    try:
        response = requests.get(BUILDBOT_URL)
        logging.info(f'{response.status_code} {BUILDBOT_URL}')
        logging.info(response.content)
        return response.status_code == 200
    except Exception as ex:
        logging.error(ex)
        logging.error(traceback.format_exc())
    logging.warning("Buildbot is down.")
    return False


def log_server_status(phab: bool, buildbot: bool, conn: psycopg2.extensions.connection):
    """log the phabricator status to the database."""
    logging.info("Writing Phabricator status to database...")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO server_status (timestamp, phabricator, buildbot) VALUES (%s,%s,%s);",
        (datetime.datetime.now(), phab, buildbot),
    )
    conn.commit()


def connect_to_db() -> psycopg2.extensions.connection:
    """Connect to the database, create tables as needed."""
    conn = psycopg2.connect(
        f"host=127.0.0.1 sslmode=disable dbname=stats user=stats password={os.getenv('DB_PASSWORD')}")
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS server_status (timestamp timestamp, phabricator boolean, buildbot boolean);"
    )
    conn.commit()
    return conn


if __name__ == "__main__":
    logging.basicConfig(level='INFO', format='%(levelname)-7s %(message)s')
    conn = connect_to_db()
    phab = phab_up()
    buildbot = buildbot_up()
    log_server_status(phab is not None, buildbot, conn)
