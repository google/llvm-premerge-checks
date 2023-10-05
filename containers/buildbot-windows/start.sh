# Checkout path is set to a fixed short value (e.g. c:\ws\src) to keep paths
# short as many tools break on Windows with paths longer than 250.

echo "start buildbot"
CC=cl CXX=cl LD=link buildbot-worker start /c/ws/buildbot