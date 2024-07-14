import csv
import glob
import re
from os.path import join

import pandas as pd

# Import parsers for specific mechanisms
from benchmark.mechanisms.bullshark import BullsharkLogParser
from benchmark.mechanisms.cometbft import CometBftLogParser
from benchmark.mechanisms.hotstuff import HotStuffLogParser


class ParseError(Exception):
    pass


class LogParser:
    def __init__(self):
        self.result_str = ""

    @classmethod
    def process(cls, directory, faults):
        assert isinstance(directory, str), "Directory path must be a string"

        clients, nodes, latency = [], [], []

        # Read client logs
        for filename in sorted(glob.glob(join(directory, "client-*.log"))):
            with open(filename, "r") as f:
                clients.append(f.read())

        # Read node logs
        for filename in sorted(glob.glob(join(directory, "node-*.log"))):
            with open(filename, "r") as f:
                nodes.append(f.read())

        # Read latency logs
        for filename in sorted(glob.glob(join(directory, "latency-*.log"))):
            with open(filename, "r") as f:
                latency.append(f.read())

        return cls(clients, nodes, latency, faults)

    def result(self):
        return self.result_str

    def print(self, filename):
        assert isinstance(filename, str), "Filename must be a string"

        print(self.result_str)

        with open(filename, "a") as f:
            f.write(self.result_str)

        result_json = self.parse_results()
        write_results_to_csv(result_json, "results.csv")

    def log_parser(self, mechanism_name, directory, faults=0):
        if mechanism_name == "hotstuff":
            result = HotStuffLogParser.process(directory, faults).result_str
        elif mechanism_name == "cometbft":
            result = CometBftLogParser.process(directory, faults).result_str
        elif mechanism_name == "bullshark":
            result = BullsharkLogParser.process(directory, faults).result_str
        else:
            raise ParseError(f"Unknown mechanism: {mechanism_name}")

        self.result_str = result

    @staticmethod
    def get_new_run_id():
        try:
            data = pd.read_csv("/home/ubuntu/geodec/results/metrics.csv")
            return data["run_id"].max() + 1
        except FileNotFoundError:
            return 1  # Return 1 if the file doesn't exist

    @staticmethod
    def aggregate_runs(run_id_array):
        data = pd.read_csv("/home/ubuntu/geodec/results/metrics.csv")

        # Filter data to include only the specified run IDs
        data = data.loc[data["run_id"].isin(run_id_array)]

        # Define the fields to average
        fields_to_avg = [
            "consensus_tps",
            "consensus_bps",
            "consensus_latency",
            "end_to_end_tps",
            "end_to_end_bps",
            "end_to_end_latency",
        ]

        # Group by 'name' and calculate the average for the specified fields
        averages = data.groupby("name")[fields_to_avg].mean().reset_index()

        # Replace the original data with the averages
        for field in fields_to_avg:
            data[field] = data["name"].map(averages.set_index("name")[field])

        # Remove duplicates, keeping only the first occurrence
        data = data.drop_duplicates(subset="name").reset_index(drop=True)

        # Add a column to indicate the number of runs aggregated
        data["runs"] = len(run_id_array)

        return data

    def parse_results(self):
        results = {}
        lines = self.result_str.split("\n")

        results["run_id"] = self.get_new_run_id()
        results["name"] = ""

        # Extract mechanism name from the summary header
        mechanism_match = re.match(r"^\s*(\w+)\s+SUMMARY:", lines[0])
        if mechanism_match:
            results["mechanism"] = mechanism_match.group(1)

        # Parsing the CONFIG section
        for line in lines:
            if line.startswith(" Faults:"):
                results["faults"] = int(line.split(":")[1].strip().split(" ")[0])
            elif line.startswith(" Input rate:"):
                results["input_rate"] = int(line.split(":")[1].strip().split(" ")[0])
            elif line.startswith(" Committee size:"):
                results["committee_size"] = int(line.split(":")[1].strip().split(" ")[0])
            elif line.startswith(" Transaction size:"):
                results["transaction_size"] = int(line.split(":")[1].strip().split(" ")[0])
            elif line.startswith(" Execution time:"):
                results["execution_time"] = int(line.split(":")[1].strip().split(" ")[0])
            elif line.startswith(" Mempool batch size:"):
                results["batch_size"] = int(line.split(":")[1].strip().split(" ")[0])

        # Parsing the RESULTS section
        for line in lines:
            if line.startswith(" Consensus TPS:"):
                results["consensus_tps"] = int(line.split(":")[1].strip().split(" ")[0])
            elif line.startswith(" Consensus BPS:"):
                results["consensus_bps"] = int(line.split(":")[1].strip().split(" ")[0].replace(",", ""))
            elif line.startswith(" Consensus latency:"):
                results["consensus_latency"] = int(line.split(":")[1].strip().split(" ")[0])
            elif line.startswith(" End-to-end TPS:"):
                results["end_to_end_tps"] = int(line.split(":")[1].strip().split(" ")[0])
            elif line.startswith(" End-to-end BPS:"):
                results["end_to_end_bps"] = int(line.split(":")[1].strip().split(" ")[0].replace(",", ""))
            elif line.startswith(" End-to-end latency:"):
                results["end_to_end_latency"] = int(line.split(":")[1].strip().split(" ")[0])

        return results


def write_results_to_csv(results, csv_filename):
    fieldnames = [
        "run_id",
        "name",
        "faults",
        "input_rate",
        "committee_size",
        "transaction_size",
        "execution_time",
        "batch_size",
        "consensus_tps",
        "consensus_bps",
        "consensus_latency",
        "end_to_end_tps",
        "end_to_end_bps",
        "end_to_end_latency",
    ]

    # Append to CSV if it exists, otherwise create it
    file_exists = False
    try:
        with open(csv_filename, "r"):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(csv_filename, "a" if file_exists else "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()  # Write header only if file doesn't exist

        writer.writerow(results)
