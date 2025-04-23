import os
import json
import pandas as pd
import logging
from datetime import datetime
import copy
import time
import subprocess
import sys

# Setup logging to both console and file
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a handler for the log file
file_handler = logging.FileHandler("processing_log.txt")
file_handler.setLevel(logging.INFO)

# Create a handler for the console (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create a formatter and attach it to both handlers
formatter = logging.Formatter("%(asctime)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Define the JSON configuration path
CONFIG_PATH = "/home/ubuntu/geodec/settings.json"
FAB_PARAMS_JSON = "/home/ubuntu/geodec/fab-params.json"

# Define the list of chains and their CSV files
CHAINS = {
    "Ethereum": "ethereum.csv",
    "Ethernodes": "ethernodes.csv",
    "Aptos": "aptos.csv",
    "Sui": "sui.csv",
    "Solana": "solana.csv",
    "Avalanche": "avalanche.csv",
}

CONSENSUS_MECHANISMS = [
    "cometbft",
    "hotstuff",
    # "bullshark"
]

GEO_INPUT_KEY = "geo_input"  # Key in the JSON where the geo_input file path is stored


def load_json_config(config_path):
    """
    Load the JSON configuration file.

    :param config_path: Path to the JSON config file.
    :return: Parsed JSON object.
    """
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load JSON configuration: {e}")
        raise


def save_json_config(config, config_path):
    """
    Save the updated JSON configuration back to the file.

    :param config: The updated JSON object.
    :param config_path: Path to save the JSON file.
    """
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        logger.info("JSON configuration saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save JSON configuration: {e}")
        raise


def update_geo_input_in_json(chain_name, consensus_name, config):
    """
    Update the 'geo_input' file path in the JSON configuration for the given chain.

    :param chain_name: Name of the chain.
    :param config: The current JSON config object.
    """
    try:
        new_geo_input = f"/home/ubuntu/geodec/rundata/{CHAINS[chain_name]}"
        df = pd.read_csv(new_geo_input)
        
        logger.info(f"Updating {GEO_INPUT_KEY} to {new_geo_input} for {chain_name}.")

        config["consensusMechanisms"][consensus_name]["geodec"][GEO_INPUT_KEY] = new_geo_input
        save_json_config(config, CONFIG_PATH)

    except Exception as e:
        logger.error(f"Failed to update geo_input in JSON for {chain_name}: {e}")
        raise
    
    return len(df)

def update_chain_config_in_json(num_nodes, consensus_name, config):
    config["remote"][consensus_name]["bench_params"]["nodes"] = [ int(num_nodes) ]
    
    save_json_config(config, FAB_PARAMS_JSON)


def process_weight_columns(input_file, consensus_name):
    """
    Processes the weight columns by renaming them to 'stake' and executing the subprocess
    for each column, then reverting the changes.

    :param input_file: The file path of the geo_input CSV file.
    :return: The processed DataFrame.
    """
    try:
        # Read the CSV file
        logger.info(f"Reading input file: {input_file}")
        df = pd.read_csv(input_file)
        original_columns = df.columns.tolist()

        # Identify weight columns
        weight_columns = [col for col in original_columns if "weight" in col.lower()]
        logger.info(f"Found {len(weight_columns)} weight columns: {weight_columns}")
        weight_columns = weight_columns[3:]
        print(weight_columns)

        addLatency = True
        
        # Process each weight column
        for weight_col in weight_columns:
            # Create a copy of the DataFrame for this iteration
            df_temp = copy.deepcopy(df)

            now = datetime.now()

            logger.info("==============================================================")
            logger.info(f"{str(now)} Running test for weight column '{weight_col}': ")

            # Rename the current weight column to "stake"
            logger.info(f"Renaming column '{weight_col}' to 'stake'")
            df_temp = df_temp.rename(columns={weight_col: "stake"})
            df_temp.to_csv(input_file, index=False)

            # Execute the subprocess and capture its output
            logger.info(f"Running subprocess for {weight_col}")
            subprocess.run(["fab", "georemote", consensus_name, str(addLatency)])


            logger.info(f"Reverting column name back to '{weight_col}'")
            logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

            # Only add the latencies for the first run
            addLatency = False
            
            # Wait before processing the next column
            time.sleep(10)

        df.to_csv(input_file, index=False)

        logger.info("All weight columns processed successfully")

        # Verify final column names match original
        if df.columns.tolist() == original_columns:
            logger.info("Final column names match original names")
        else:
            logger.warning("Final column names differ from original names")

        return df

    except Exception as e:
        logger.error(f"Error processing weight columns: {e}")
        raise


def process_all_chains(consensus_name):
    """
    Iterates over all chains, updating the geo_input path in JSON,
    and processing the weight columns for each one.
    """
    try:
        # Load the JSON configuration
        config = load_json_config(CONFIG_PATH)
        chain_config = load_json_config(FAB_PARAMS_JSON)

        for chain in CHAINS:
            logger.info(f"Processing chain: {chain}")

            # Update the geo_input path in the JSON for the current chain
            num_nodes = update_geo_input_in_json(chain, consensus_name, config)
            
            # Update the node count in the Fab params JSON for the current chain
            update_chain_config_in_json(num_nodes, consensus_name, chain_config)

            # Get the updated geo_input file path from the config
            input_file = config["consensusMechanisms"][consensus_name]["geodec"][GEO_INPUT_KEY]

            # Process the weight columns for the current geo_input CSV
            process_weight_columns(input_file, consensus_name)

        logger.info("Processing completed for all chains successfully")

    except Exception as e:
        logger.error(f"Program failed during processing: {e}")
        raise


if __name__ == "__main__":
    for consensus_name in CONSENSUS_MECHANISMS:
        logger.info(f"Processing consensus: {consensus_name}")
        process_all_chains(consensus_name)
