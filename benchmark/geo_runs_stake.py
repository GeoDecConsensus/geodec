import os
import json
import pandas as pd
import logging
from datetime import datetime
import copy
import time
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

# Define the JSON configuration path
CONFIG_PATH = "/home/ubuntu/geodec/settings.json"  # Replace with actual path

# Define the list of consensus mechanisms and their CSV files
CONSENSUS_MECHANISMS = {
    "Solana": "solana.csv",
    "Aptos": "aptos.csv",
    "Avalanche": "avalanche.csv",
    "Sui": "sui.csv",
    "Ethereum": "ethereum.csv",
    "Ethernode": "ethernode.csv",
}

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


def update_geo_input_in_json(consensus_name, config):
    """
    Update the 'geo_input' file path in the JSON configuration for the given consensus mechanism.

    :param consensus_name: Name of the consensus mechanism.
    :param config: The current JSON config object.
    """
    try:
        new_geo_input = f"/home/ubuntu/geodec/rundata/{CONSENSUS_MECHANISMS[consensus_name]}"
        logger.info(f"Updating {GEO_INPUT_KEY} to {new_geo_input} for {consensus_name}.")

        config["consensusMechanisms"]["hotstuff"]["geodec"][GEO_INPUT_KEY] = new_geo_input
        save_json_config(config, CONFIG_PATH)

    except Exception as e:
        logger.error(f"Failed to update geo_input in JSON for {consensus_name}: {e}")
        raise


def process_weight_columns(input_file):
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
        df = df.rename(columns={"server_id": "id"})
        original_columns = df.columns.tolist()

        # Identify weight columns
        weight_columns = [col for col in original_columns if "weight" in col.lower()]
        logger.info(f"Found {len(weight_columns)} weight columns: {weight_columns}")

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

            # Execute the subprocess (assumed fab command)
            logger.info(f"Running subprocess for {weight_col}")
            subprocess.run(["fab", "georemote", "hotstuff"])

            logger.info(f"Reverting column name back to '{weight_col}'")
            logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

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


def process_all_consensus_mechanisms():
    """
    Iterates over all consensus mechanisms, updating the geo_input path in JSON,
    and processing the weight columns for each one.
    """
    try:
        # Load the JSON configuration
        config = load_json_config(CONFIG_PATH)

        for consensus in CONSENSUS_MECHANISMS:
            logger.info(f"Processing consensus mechanism: {consensus}")

            # Update the geo_input path in the JSON for the current consensus
            update_geo_input_in_json(consensus, config)

            # Get the updated geo_input file path from the config
            input_file = config["consensusMechanisms"]["hotstuff"]["geodec"][GEO_INPUT_KEY]

            # Process the weight columns for the current geo_input CSV
            process_weight_columns(input_file)

        logger.info("Processing completed for all consensus mechanisms successfully")

    except Exception as e:
        logger.error(f"Program failed during processing: {e}")
        raise


if __name__ == "__main__":
    process_all_consensus_mechanisms()
