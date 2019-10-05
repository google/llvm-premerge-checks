#!/usr/bin/python3
import datetime
import os
import shutil

ROOT_DIR = '/mnt/nfs/results'
MAX_AGE = datetime.timedelta(days=90)
MAX_AGE_BIN = datetime.timedelta(days=3)

now = datetime.datetime.now()

for folder in [f for f in os.listdir(ROOT_DIR)]:
    fullpath = os.path.join(ROOT_DIR, folder)
    if not os.path.isdir(fullpath):
        continue
    print(fullpath)
    binpath = os.path.join(ROOT_DIR, folder, 'binaries')
    stats=os.stat('/tmp')    
    created = datetime.datetime.fromtimestamp(stats.st_mtime)
    print(created)
    if created + MAX_AGE < now:
        print("Deleting all results: {}".format(fullpath))
        shutil.rmtree(fullpath)
    elif os.path.exists(binpath) and created + MAX_AGE_BIN < now:
        print("Deleting binaries: {}".format(binaries))
        shutil.rmtree(binpath)