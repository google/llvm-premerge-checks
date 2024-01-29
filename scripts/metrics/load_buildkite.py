import sys
import psycopg2
import psycopg2.extras
import logging
import requests
import os
import dateutil
import chardet
from benedict import benedict
import traceback

psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

token = f'Bearer {os.getenv("BUILDKITE_API_TOKEN")}'


def connect():
    return psycopg2.connect(
        f"host=127.0.0.1 sslmode=disable dbname=stats user=stats password={os.getenv('DB_PASSWORD')}")


def download_text(url):
    r = requests.get(url, allow_redirects=True,
                     headers={'Authorization': token})
    if r.status_code != 200:
        raise Exception(f'response status {r.status_code}')
    try:
        return r.content.decode('utf-8').replace("\x00", "\uFFFD"), 'utf-8'
    except:
        pass
    try:
        return r.content.decode('ascii').replace("\x00", "\uFFFD"), 'ascii'
    except:
        pass
    d = chardet.detect(r.content)
    return r.content.decode(d['encoding']).replace("\x00", "\uFFFD"), d['encoding']


def download_job_logs(conn):
    logging.info('downloading job logs')
    with conn.cursor() as c:
        c.execute(f"""
select j.id, j.raw->>'raw_log_url' url
from jobs j
left join artifacts a on a.job_id = j.id and a.id=j.id
where a.id IS NULL and j.raw->>'raw_log_url' IS NOT NULL
""")
        total = c.rowcount
        logging.info(f'will download {total} logs')
        cnt = 0
        for row in c:
            cnt += 1
            job_id = row[0]
            url = row[1]
            meta = {'filename': 'stdout'}
            try:
                content, en = download_text(url)
                meta['encoding'] = en
                with conn.cursor() as i:
                    i.execute('INSERT INTO artifacts (id, job_id, content, meta) VALUES (%s, %s, %s, %s)',
                              [job_id, job_id, content, meta])
            except:
                meta['failure'] = traceback.format_exc()
                logging.error(f'download artifact failed {meta["failure"]} {url}')
                with conn.cursor() as i:
                    i.execute('INSERT INTO artifacts (id, job_id, meta) VALUES (%s, %s, %s)', [job_id, job_id, meta])
            if cnt % 100 == 0:
                logging.info(f'downloaded {cnt}/{total} logs')
            conn.commit()
        logging.info(f'downloaded {cnt} logs')
    return True


def download_job_artifacts(conn):
    logging.info('downloading job artifacts')
    with conn.cursor() as c:
        c.execute(f"""
select ja.meta from
(select j.key,j.id job_id, a->>'id' aid, a as meta from jobs j, json_array_elements(j.meta->'artifacts') as a) as ja
left join artifacts a on a.job_id = ja.job_id and a.id=ja.aid
where a.id IS NULL""")
        total = c.rowcount
        logging.info(f'will download {total} artifacts')
        cnt = 0
        for row in c:
            meta = benedict(row[0])
            cnt += 1
            try:
                content, en = download_text(meta.get('download_url'))
                meta['encoding'] = en
                with conn.cursor() as i:
                    i.execute('INSERT INTO artifacts (id, job_id, content, meta) VALUES (%s, %s, %s, %s)',
                              [meta.get('id'), meta.get('job_id'), content, meta])
            except:
                meta['failure'] = traceback.format_exc()
                logging.error(f'download artifact failed {meta["failure"]} {meta.get("download_url")}')
                with conn.cursor() as i:
                    i.execute('INSERT INTO artifacts (id, job_id, meta) VALUES (%s, %s, %s)',
                              [meta.get('id'), meta.get('job_id'), meta])
            if cnt % 100 == 0:
                logging.info(f'downloaded {cnt}/{total} artifacts')
            conn.commit()
        logging.info(f'downloaded {cnt} artifacts')
    return True


def insert_new_builds(conn):
    logging.info('inserting new builds')
    all_builds = []
    page = 1
    while page < 10000:
        logging.info(f'checking page #{page}')
        re = requests.get('https://api.buildkite.com/v2/organizations/llvm-project/builds',
                          params={'page': page},
                          headers={'Authorization': token})
        if re.status_code != 200:
            logging.error(f'list builds response status: {re.status_code}')
            sys.exit(1)
        x = re.json()
        if not x:
            logging.warning('empty response')
            break
        page += 1
        all_builds.extend(x)
        b = x[-1]
        with conn.cursor() as c:
            c.execute('SELECT count(1) FROM builds WHERE id = %s', (b.get('id'),))
            if c.fetchone()[0] != 0:
                logging.info(f"found existing build {b.get('id')}")
                break
    all_builds.reverse()
    logging.info(f'{len(all_builds)} builds loaded')
    cnt = 0
    for b in all_builds:
        with conn.cursor() as c:
            c.execute('INSERT INTO builds (id, raw) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET raw = %s',
                      [b.get('id'), b, b])
            cnt += 1
            if cnt % 100 == 0:
                logging.info(f'{cnt} builds inserted / updated')
                conn.commit()
    conn.commit()
    logging.info(f'{cnt} builds inserted')
    return cnt


def insert_all_builds(conn):
    logging.info('inserting all builds')
    page = 1
    cnt = 0
    while page < 100000:
        logging.info(f'checking page #{page}')
        re = requests.get('https://api.buildkite.com/v2/organizations/llvm-project/builds',
                          params={'page': page},
                          headers={'Authorization': token})
        if re.status_code != 200:
            logging.error(f'list builds response status: {re.status_code}')
            sys.exit(1)
        x = re.json()
        if not x:
            logging.warning('empty response')
            break
        page += 1
        for b in x:
            with conn.cursor() as c:
                c.execute('SELECT count(1) FROM builds WHERE id = %s', (b.get('id'),))
                if c.fetchone()[0] == 0:
                    c.execute('INSERT INTO builds (id, raw) VALUES (%s, %s)', [b.get('id'), b])
                    cnt += 1
                    if cnt % 100 == 0:
                        logging.info(f'{cnt} builds inserted')
                        conn.commit()
    conn.commit()
    logging.info(f'{cnt} builds inserted')
    return cnt


def update_running_builds(conn):
    with conn.cursor() as c:
        c.execute("""
SELECT key, raw
FROM builds b
WHERE b.raw->>'state' IN ('running', 'scheduled', 'canceling')""")
        cnt = 0
        total = c.rowcount
        logging.info(f'checking {total} running builds')
        for row in c:
            key = row[0]
            raw = row[1]
            logging.info(f'running build {key}')
            re = requests.get(raw['url'], headers={'Authorization': token})
            logging.info(f"{raw['url']} -> {re.status_code}")
            if re.status_code != 200:
                # mark build as "invalid"
                continue
            j = re.json()
            logging.info(f"state {raw['state']} -> {j['state']}")
            with conn.cursor() as u:
                u.execute("""UPDATE builds SET raw = %s WHERE key = %s""", (j, key))
            cnt += 1
            if cnt % 100 == 0:
                conn.commit()
    conn.commit()


def download_job_artifacts_list(conn):
    logging.info('download jobs artifact lsits')
    with conn.cursor() as c:
        c.execute("""
SELECT key, raw->>'artifacts_url', meta
FROM jobs
WHERE (meta->>'artifacts' IS NULL) AND (raw->>'artifacts_url' IS NOT NULL)""")
        cnt = 0
        total = c.rowcount
        logging.info(f'will download {total} artifact lists')
        for row in c:
            key = row[0]
            url = row[1]
            meta = row[2]
            if meta is None:
                meta = {}
            r = requests.get(url, allow_redirects=True, headers={'Authorization': token})
            if r.status_code != 200:
                logging.error(f'cannot load artifacts_url {r.status_code} {url}')
                continue
            meta['artifacts'] = r.json()
            with conn.cursor() as i:
                i.execute('UPDATE jobs SET meta = %s WHERE key = %s', (meta, key))
            cnt += 1
            if cnt % 100 == 0:
                logging.info(f'downloaded {cnt}/{total} artifact lists')
                conn.commit()
        logging.info(f'downloaded {cnt} artifact lists')
        conn.commit()


def insert_new_jobs(conn):
    logging.info('inserting new jobs')
    with conn.cursor() as c:
        c.execute("""select bj.id, bj.jid, bj.job from
(select b.id, j->>'id' jid, j as job from builds b, json_array_elements(b.raw->'jobs') as j
WHERE b.raw->>'state' NOT IN ('running', 'scheduled', 'canceling')) as bj
left join jobs j on j.id = bj.jid
where j.id IS NULL""")
        total = c.rowcount
        cnt = 0
        logging.info(f'will insert {total} jobs')
        for row in c:
            build_id = row[0]
            job_id = row[1]
            job = benedict(row[2])
            meta = {}
            # durations
            runnable_at = job.get('runnable_at')
            started_at = job.get('started_at')
            finished_at = job.get('finished_at')
            if (runnable_at is not None) and (started_at is not None) and (finished_at is not None):
                runnable_at = dateutil.parser.parse(runnable_at)
                started_at = dateutil.parser.parse(started_at)
                finished_at = dateutil.parser.parse(finished_at)
                meta['queue_time'] = (started_at - runnable_at).total_seconds()
                meta['run_time'] = (finished_at - started_at).total_seconds()
                meta['total_time'] = (finished_at - runnable_at).total_seconds()
            # agent data
            for e in job.get('agent.meta_data', []):
                p = e.split('=')
                if p[0] == 'queue':
                    meta['agent_queue'] = p[1]
                if p[0] == 'name':
                    meta['agent_name'] = p[1]
            with conn.cursor() as i:
                i.execute('INSERT INTO jobs (id, build_id, raw, meta) VALUES (%s, %s, %s, %s)',
                          [job_id, build_id, job, meta])
            cnt += 1
            if cnt % 100 == 0:
                logging.info(f'inserted {cnt}/{total} jobs')
                conn.commit()
        logging.info(f'inserted {cnt} jobs')
        conn.commit()


if __name__ == '__main__':
    logging.basicConfig(level='INFO', format='%(levelname)-7s %(message)s')
    cn = connect()
    logging.info('downloading buildkite data')
    # insert_all_builds(cn)
    # insert_new_builds(cn)
    # update_running_builds(cn)
    # insert_new_jobs(cn)
    # download_job_artifacts_list(cn)
    # download_job_artifacts(cn)
    # download_job_logs(cn)
