#!/bin/bash

SSD_ROOT="/mnt/disks/ssd0"
AGENT_ROOT="${SSD_ROOT}/agent"

# prepare root folder for Jenkins agent
mkdir -p "${AGENT_ROOT}"
chown -R jenkins:jenkins "${AGENT_ROOT}"

# TODO(kuhnel): wipe the disk on startup
# TODO(kuhnel): move ccache to SDD

# start ssh server
/usr/sbin/sshd -D