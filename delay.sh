#!/bin/bash

option=$1
delay=$2
jitters=$3

# option 1 means adding a default delay for everything
if [ $option -eq 1 ]; then
    sudo tc qdisc change dev eth0 root netem delay ${delay}ms ${jitters}ms # 30ms jitters
fi
