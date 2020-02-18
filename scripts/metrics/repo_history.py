#!/usr/bin/env python3

import sqlite3
import os

conn = sqlite3.connect(os.path.expanduser('~/llvm-propject.db'))
c = conn.cursor()

c.execute('CREATE TABLE repo (hash text)')
conn.commit()