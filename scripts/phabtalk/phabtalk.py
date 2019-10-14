#!/usr/bin/env python3
from phabricator import Phabricator


class PhabTalk:

    def __init__(self):
        self._phab = Phabricator()

    def get_revision_id

def main(phid: str, diff: str):
    result = phab.differential.querydiffs(ids=[diff])
    return 'D'+result[diff]['revisionID'])


if __name__ == '__main__':
    main('PHID-HMBT-vitgimipuq4ntrmacw67','223623')