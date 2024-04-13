# GeoDec: Enhancing Blockchain Resilience through Geospatial Validator Distribution

GeoDec aims to address the geographic concentration of validator nodes in existing blockchain networks, particularly in the context of PoS consensus mechanisms. The project involves the development of an emulator to analyze geospatial distribution, the design of a geospatial-aware proposer selection mechanism, and deploying the revised protocol for evaluation.

This repo is a fork of the original repo, served solely for the purpose of benchmarking cometbft performance.

### Requirement
The use of this repo requires the installation of https://www.fabfile.org/index.html#welcome-to-fabric.

### Usage
To test cometbft performance using your own machines, settings, and cometbft code branch, make the following changes.
1. testdata/IP.txt: Change the content to the IPs of your machines
2. testdata/instances_ip.csv: Change the content to the IPs of your machines. Enter the internal IP two times if there is no external IP in your case.
3. settings.json: This JSON file contains the configuration for geodec. Modify the repo section to use your own cometbft code.

After modifying the required configuration, run ```fab remote cometbft``` to start the benchmark.

### References
- Motepalli, Shashank, and Hans-Arno Jacobsen. "Analyzing Geospatial Distribution in Blockchains." arXiv preprint arXiv:2305.17771 (2023).
- Nodetracker on Etherscan, https://etherscan.io/nodetracker, accessed 25th January 2024.
- Censorship pics, https://censorship.pics/, accessed 25th January 2024.

### Credits
Thanks to [Alberto Sonnino](https://github.com/asonnino) for the initial hotstuff benchmark.
