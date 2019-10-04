#!/bin/bash
set -eux

# to detatch:
# gcloud compute instances detach-disk --disk=jenkins-home <HOST>
gcloud compute disks delete jenkins-home