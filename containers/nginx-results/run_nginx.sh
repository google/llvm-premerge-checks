#!/bin/bash
set -eux

mkdir -p /mnt/nfs/results
chmod 777 /mnt/nfs/results
cp /scripts/*.html /mnt/nfs/results
nginx -g "daemon off;"