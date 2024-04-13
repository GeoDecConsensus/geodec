#!/bin/bash

# Define the IP addresses
IP_ADDRESSES=("192.168.41.39", "192.168.41.237", "192.168.41.64", "192.168.41.193")
GEODEC="cometbft_geodec"
BROADCAST="cometbft_broadcast"

# Read command line variable
USE_GEODEC="$1"

# Function to perform SSH and mv operation
use_broadcast() {
    local ip=$1
    ssh -i ~/.ssh/geodec ubuntu@$ip "cd ~ && mv cometbft $GEODEC && mv $BROADCAST cometbft"
}

use_geodec() {
    local ip=$1
    ssh -i ~/.ssh/geodec ubuntu@$ip "cd ~ && mv cometbft $BROADCAST && mv $GEODEC cometbft"
}

# Iterate over each IP address and perform the move operation
for ip_address in "${IP_ADDRESSES[@]}"; do
    if [ "$USE_GEODEC" = "1" ]; then
        check_res=$(ssh -i ~/.ssh/geodec ubuntu@$ip_address "[ -d \"$GEODEC\" ] && echo 'ok' || echo 'not ok'")
        if [[ "$ssh_output" == "ok" ]]; then
            echo "use geodec " $ip_address
            use_geodec $ip_address
        else
            echo "already using geodec"
        fi
    else
        check_res=$(ssh -i ~/.ssh/geodec ubuntu@$ip_address "[ -d \"$BROADCAST\" ] && echo 'ok' || echo 'not ok'")
        if [[ "$ssh_output" == "ok" ]]; then
            echo "use broadcast"
            use_broadcast $ip_address
        else
            echo "already using broadcast"
        fi
    fi
done
