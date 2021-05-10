#!/usr/bin/env python3
import os
import psycopg2
import git
from repo_hist import MyCommit
import datetime
import csv
from typing import Set

# TODO: make his path configurable for use on the server
REPO_DIR = "tmp/llvm-project"
GIT_URL = "https://github.com/llvm/llvm-project.git"
GIT_BRANCH = "main"
OUTPUT_PATH = "tmp"

# this was the start of using git as primary repo
MAX_AGE = datetime.datetime(year=2019, month=10, day=1, tzinfo=datetime.timezone.utc)


def connect_to_db() -> psycopg2.extensions.connection:
    """Connect to the database, return connection object."""
    conn = psycopg2.connect(
        "host=127.0.0.1 sslmode=disable dbname=stats user={} password={}".format(
            os.environ["PGUSER"], os.environ["PGPASSWORD"]
        )
    )
    return conn


def create_tables(conn: psycopg2.extensions.connection):
    """Create database tables if needed."""
    # TODO: add more attributes as needed
    # TODO: add all projects as columns
    print("Creating tables as needed...")
    cur = conn.cursor()
    # mod_<project> column: files in the subfolder (=project) <project> were
    # modified by this commit.
    # git hashes are 40 characters long, so using char(40) data type here
    cur.execute(
        """ CREATE TABLE IF NOT EXISTS git_commits (
                                        hash char(40) PRIMARY KEY,
                                        commit_time timestamp,
                                        phab_id text,
                                        reverts_hash char(40),
                                        mod_llvm boolean,
                                        mod_clang boolean,
                                        mod_libcxx boolean,
                                        mod_mlir boolean
                                    ); """
    )

    conn.commit()


def get_existing_hashes(conn: psycopg2.extensions.connection) -> Set[str]:
    """Fetch all stored git hashes from the database."""
    print("Fetching known git hashes from the database...")
    cur = conn.cursor()
    cur.execute("SELECT hash from git_commits;")
    return set((row[0] for row in cur.fetchall()))


def update_repo(repo_dir: str) -> git.Repo:
    """Clone or fetch local copy of the git repository."""
    if os.path.isdir(repo_dir):
        print("Fetching git repo...")
        repo = git.Repo(repo_dir)
        repo.remotes.origin.fetch(GIT_BRANCH)
    else:
        print("Cloning git repo...")
        git.Repo.clone_from(GIT_URL, repo_dir, bare=True)
        repo = git.Repo(repo_dir)
    print("repo update done.")
    return repo


def parse_commits(
    conn: psycopg2.extensions.connection, repo: git.Repo, max_age: datetime.datetime
):
    """Parse the git repo history and upload it to the database."""

    sql_insert_commit = """ INSERT INTO 
          git_commits (hash, commit_time, phab_id, reverts_hash) 
          values (%s,%s,%s,%s);
          """
    sql_update_commit_project = (
        """ UPDATE git_commits SET mod_{} = %s where hash = %s;"""
    )
    known_hashes = get_existing_hashes(conn)
    day = None
    cur = conn.cursor()
    for commit in repo.iter_commits(GIT_BRANCH):
        # TODO: This takes a couple of minutes, maybe try using multithreading

        # Only store new/unknown hashes
        if commit.hexsha in known_hashes:
            continue
        if commit.committed_datetime < max_age:
            break
        mycommit = MyCommit(commit)
        if mycommit.date.day != day:
            # take a snapshot commit, nice to see progress while updating the
            # database
            day = mycommit.date.day
            print(mycommit.date)
            conn.commit()
        cur.execute(
            sql_insert_commit,
            (
                mycommit.chash,
                mycommit.date,
                mycommit.phab_revision,
                mycommit.reverts_commit_hash,
            ),
        )
        # Note: prasing the patches is quite slow
        for project in mycommit.modified_projects:
            # TODO find a way to make this generic for all projects, maybe user
            # "ALTER TABLE" to add columns as they appear
            # TODO: modifying the commited row is expensive, maybe find something faster
            if project in ["llvm", "libcxx", "mlir", "clang"]:
                cur.execute(
                    sql_update_commit_project.format(project), (True, mycommit.chash)
                )
    conn.commit()


def create_csv_report(title: str, query: str, output_path: str):
    cursor = conn.cursor()
    data = cursor.execute(query)
    with open(os.path.join(output_path, title + ".csv"), "w") as csv_file:
        writer = csv.writer(csv_file)
        # write column headers
        writer.writerow([description[0] for description in cursor.description])
        for row in data:
            writer.writerow(row)


def run_queries(conn: psycopg2.extensions.connection, output_path: str):
    print("running queries...")
    create_csv_report("full_db_dump", "select * from commits;", output_path)

    query = """SELECT strftime('%Y-%m',commit_time) as month, count(hash) as num_commits, count(phab_id) as num_reviewed, 
            (100.0*count(phab_id)/count(hash)) as percent_reviewed, count(reverts_hash) as num_reverted, 
            (100.0*count(reverts_hash)/count(hash)) as percent_reverted
          FROM commits
          WHERE mod_{}
          GROUP BY month;
          """
    create_csv_report("libcxx_stats", query.format("libcxx"), output_path)
    create_csv_report("mlir_stats", query.format("mlir"), output_path)

    query = """SELECT strftime('%Y-%m',commit_time) as month, count(hash) as num_commits, count(phab_id) as num_reviewed, 
            (100.0*count(phab_id)/count(hash)) as percent_reviewed, count(reverts_hash) as num_reverted, 
            (100.0*count(reverts_hash)/count(hash)) as percent_reverted
          FROM commits
          GROUP BY month;
          """
    create_csv_report("all_projects_stats", query, output_path)


def update_comits():
    """Update the git commits in the database from the git repository."""
    repo = update_repo(REPO_DIR)
    conn = connect_to_db()
    create_tables(conn)
    parse_commits(conn, repo, MAX_AGE)


if __name__ == "__main__":
    update_comits()
    # TODO: add argparse to switch between import and query mode or
    # move queries to another file
    # run_queries(conn)
