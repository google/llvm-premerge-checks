#!/usr/bin/env python3
import os
import sqlite3
import git
from repo_hist import MyCommit
import datetime
import csv

DB_PATH = "tmp/git_hist.sqlite"
REPO_DIR = "tmp/llvm-project"
GIT_URL = "https://github.com/llvm/llvm-project.git"
GIT_BRANCH = "main"
OUTPUT_PATH = "tmp"

# this was the start of using git as primary repo
MAX_AGE = datetime.datetime(year=2019, month=10, day=1, tzinfo=datetime.timezone.utc)
# Maximum age of the database before we re-create it
DB_UPDATE_INTERVAL = datetime.timedelta(days=1)


def popolate_db(
    db_path: str, repo_dir: str, max_age: datetime.datetime
) -> sqlite3.Connection:
    # TODO: full scan of the git history is quite slow. Maybe enable incremental
    #  updates. Only insert commits that are not yet in the database.
    if os.path.exists(db_path):
        age = datetime.datetime.now() - datetime.datetime.fromtimestamp(
            os.path.getmtime(db_path)
        )
        if age < DB_UPDATE_INTERVAL:
            print("Database is recent enough, using existing one.")
            return sqlite3.connect(db_path)
        os.remove(db_path)

    print("Database is stale, needs updating...")
    conn = sqlite3.connect(db_path)
    print("Creating tables...")
    create_tables(conn)
    print("Scanning repository...")
    parse_commits(conn, repo_dir, max_age)
    print("Done populating database.")
    return conn


def create_tables(conn: sqlite3.Connection):
    # TODO: add more attributes as needed
    # TODO: add all projects as columns
    # mod_<project> column: files in the subfolder (=project) <project> were
    # modified by this commit.
    conn.execute(
        """ CREATE TABLE IF NOT EXISTS commits (
                                        hash string PRIMARY KEY,
                                        commit_time integer,
                                        phab_id string,
                                        reverts_hash string,
                                        mod_llvm boolean,
                                        mod_clang boolean,
                                        mod_libcxx boolean,
                                        mod_mlir boolean
                                    ); """
    )

    conn.commit()


def parse_commits(conn: sqlite3.Connection, repo_dir: str, max_age: datetime.datetime):
    if os.path.isdir(repo_dir):
        print("Fetching git repo...")
        repo = git.Repo(repo_dir)
        repo.remotes.origin.fetch(GIT_BRANCH)
    else:
        print("Cloning git repo...")
        git.Repo.clone_from(GIT_URL, repo_dir, bare=True)
        repo = git.Repo(repo_dir)
    print("repo update done.")
    sql_insert_commit = """ INSERT INTO 
          commits (hash, commit_time, phab_id, reverts_hash) 
          values (?,?,?,?);
          """
    sql_update_commit_project = """ UPDATE commits SET mod_{} = ? where hash = ?;"""

    day = None
    for commit in repo.iter_commits(GIT_BRANCH):
        # TODO: This takes a couple of minutes, maybe try using multithreading
        if commit.committed_datetime < max_age:
            break
        mycommit = MyCommit(commit)
        if mycommit.date.day != day:
            day = mycommit.date.day
            print(mycommit.date)
            # take a snapshot commit, nice to see progress while updating the
            # database
            conn.commit()
        conn.execute(
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
            if project in ["llvm", "libcxx", "mlir", "clang"]:
                conn.execute(
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


def run_queries(conn: sqlite3.Connection, output_path: str):
    print("running queries...")
    create_csv_report("full_db_dump", "select * from commits;", output_path)
    query = """SELECT strftime('%Y-%m',commit_time) as month, count(hash) as num_commits, count(phab_id) as num_reviewed, 
            (100.0*count(phab_id)/count(hash)) as percent_reviewed, count(reverts_hash) as num_reverted, 
            (100.0*count(reverts_hash)/count(hash)) as percent_reverted
          FROM commits
          WHERE mod_libcxx
          GROUP BY month;
          """
    create_csv_report("libcxx_stats", query, output_path)
    query = """SELECT strftime('%Y-%m',commit_time) as month, count(hash) as num_commits, count(phab_id) as num_reviewed, 
            (100.0*count(phab_id)/count(hash)) as percent_reviewed, count(reverts_hash) as num_reverted, 
            (100.0*count(reverts_hash)/count(hash)) as percent_reverted
          FROM commits
          GROUP BY month;
          """
    create_csv_report("all_projects_stats", query, output_path)


if __name__ == "__main__":
    conn = popolate_db(DB_PATH, REPO_DIR, MAX_AGE)
    run_queries(conn, OUTPUT_PATH)
