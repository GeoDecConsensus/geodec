#!/bin/bash

# Check if at least one IP address is provided
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <ip_address1> [ip_address2] [ip_address3] ..."
    exit 1
fi

# Initialize the final result string
final_result=""

BASE_COMMAND="/home/ubuntu/cometbft show_node_id --home ./mytestnet/node"

# Iterate through the provided IP addresses
for ((i=1; i<=$#; i++)); do
    ip_address="${!i}"  # Get the value of the current argument (IP address)
    NODE_IDX=$((i - 1)) 
    iteration_number=$NODE_IDX  # Use the iteration number (0-based)

    ID=$($BASE_COMMAND$iteration_number)

    # Run your command here using the IP address and iteration number
    # For example, replace the following line with your actual command
    # result=$(ssh user@$ip_address "your_command $iteration_number")
    result="$ID@$ip_address:26656"

    # Concatenate the result to the final string
    final_result+=",$result"
done

# Remove the leading comma
final_result="${final_result:1}"

# Print the final result
echo "Final Result: $final_result"

echo "$final_result" > persistent_peer.txt
