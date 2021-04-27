#!/usr/bin/env python3
import os
import sqlite3
import git
from repo_hist import MyCommit
import datetime

DB_PATH = "tmp/git_hist.sqlite"
REPO_DIR = "tmp/llvm-project"
GIT_URL = "https://github.com/llvm/llvm-project.git"
GIT_BRANCH = "main"
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
    print("Creating indexes...")
    create_indexes(conn)
    print("Scanning repository...")
    parse_commits(conn, repo_dir, max_age)
    print("Done populating database.")
    return conn


def create_tables(conn: sqlite3.Connection):
    # TODO: add more attributes as needed
    conn.execute(
        """ CREATE TABLE IF NOT EXISTS commits (
                                        hash string PRIMARY KEY,
                                        commit_time integer,
                                        phab_id string,
                                        reverts_hash string
                                    ); """
    )
    # Normalized representation of modified projects per commit.
    conn.execute(
        """ CREATE TABLE IF NOT EXISTS commit_project (
                                      project string,
                                      hash string,
                                      FOREIGN KEY (hash) REFERENCES commits(hash)
                                    );"""
    )

    conn.commit()


def create_indexes(conn: sqlite3.Connection):
    """Indexes to speed up searches and joins."""
    conn.execute(
        """ CREATE INDEX commit_project_hash
            ON commit_project(hash);"""
    )
    conn.execute(
        """ CREATE INDEX commit_project_project
            ON commit_project(project);"""
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
    sql_insert_commit_project = """ INSERT INTO 
          commit_project (hash, project) 
          values (?,?);
          """
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
            conn.execute(sql_insert_commit_project, (mycommit.chash, project))
    conn.commit()


def run_queries(conn: sqlite3.Connection):
    query = """SELECT commits.hash, commits.phab_id, commits.commit_time
          FROM commits 
          INNER JOIN commit_project ON commits.hash = commit_project.hash
          WHERE commit_project.project="libcxx";"""
    cursor = conn.cursor()
    data = cursor.execute(query)
    for row in data:
        print(row)


if __name__ == "__main__":
    conn = popolate_db(DB_PATH, REPO_DIR, MAX_AGE)
    run_queries(conn)
