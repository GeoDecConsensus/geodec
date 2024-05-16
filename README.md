# GeoDec

GeoDec aims to address the geographic concentration of validator nodes in existing blockchain networks, particularly in the context of PoS consensus mechanisms. The project involves the development of an emulator to analyze geospatial distribution.

<b> Geodec is in active development. </b> Please open an issue if you would like to contribute.

## Table of Contents

-   [Table of Contents](#table-of-contents)
-   [Get Started](#get-started)
-   [How does it work?](#how-does-it-work)
    -   [`Remote`](#remote)
    -   [`Geodec`](#geodec)
-   [Development](#development)
-   [Demo](#demo)
-   [Maintainers](#maintainers)
-   [Contributing](#contributing)
-   [License](#license)
-   [Relevant Work](#relevant-work)
-   [Credits](#credits)

## Get Started

### Pre-requisites

-   Cometbft and Hotstuff (or Bullshark - same configs) is required to create the node config files.
-   Rust
-   Python3

For cometbft you can use the binary (light weight and easy) \
For hotstuff you need to clone the repo and install cargo rust

Clone hotstuff

```bash
git clone https://github.com/GeoDecConsensus/hotstuff.git
```

Clone cometbft binary

```bash
# Download the tar.gz file using curl
curl -LO https://github.com/cometbft/cometbft/releases/download/v1.0.0-alpha.2/cometbft_1.0.0-alpha.2_linux_amd64.tar.gz

# Create a directory for cometbft
mkdir cometbft-dir

# Extract the tar.gz file into the newly created directory
tar xvf cometbft_1.0.0-alpha.2_linux_amd64.tar.gz -C cometbft-dir

# Move the cometbft binary to the current directory
mv cometbft-dir/cometbft ./

# Remove the downloaded tar.gz file and the directory
rm -r cometbft_1.0.0-alpha.2_linux_amd64.tar.gz cometbft-dir
```

Install rust (non-interactive)

```bash
curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustup default stable
```

### Download Geodec

```bash
git clone https://github.com/GeoDecConsensus/geodec.git
cd geodec
pip install -r requirements.txt
```

## How does it work?

Geodec supports the following consensus mechanisms:

-   Cometbft - https://github.com/cometbft/cometbft
-   Hotstuff - https://github.com/asonnino/hotstuff
-   Bullshark - https://github.com/asonnino/narwhal/tree/bullshark

### Remote

The `remote` command is used to run the consensus mechanism on a cluster of `n` nodes.

```bash
fab remote <mechanism_name> # ["cometbft", "hotstuff", "bullshark"]
```

### GeoRemote

The `georemote` command is used to run the consensus mechanism on a cluster of `n` nodes with added artificial latencies. The artificial latency is added to simulate the geographic distribution of the nodes. The latency data is taken from [WonderProxy](https://wonderproxy.com/blog/a-day-in-the-life-of-the-internet/)

```bash
fab georemote <mechanism_name> # ["cometbft", "hotstuff", "bullshark"]
```

## File Structure

-   Run data

    -   `cometbft-config.toml` - For any custom configuration for the cometbft consensus mechanism if needed.
    -   `instances_ip.csv` - Contains the IP addresses of the node instances.
    -   `geo-input.csv` - Tells the artificial location of the nodes. The first column **ID** - server id and the second column **Count** - number of nodes in that location.
    -   `servers.csv` - Contains the geographical data of servers. NO NEED TO CHANGE THIS FILE.
    -   `ping_grouped.csv` - Contains the latency data of the servers. NO NEED TO CHANGE THIS FILE.

-   `fab-param.json` - Contains the bencha and node parameters for the consensus mechanism. Used in the `fabfile.py` file.
-   `fabfile.py` - Contains the fabric commands like install, remote, georemote. NO NEED TO CHANGE THIS FILE.
-   `settings.json` - Contains the settings related to locations of keys, file, ports, etc.
-   `persistent.sh` - Bash script to generate the persistent peers for the cometbft. NO NEED TO CHANGE THIS FILE.

## Demo

Demo of geodec running the remote and geodec

## Maintainers

[Naman Garg](https://x.com/namn_grg)

[Shashank Motepalli](https://x.com/sh1sh1nk)

## Contributing

Feel free to open issues, wait to receive confirmation from the maintainers before starting to work on it.

## License

This project is licensed under the Apache License - see the [LICENSE.md](LICENSE) file for details.

## Relevant Work

-   Motepalli, Shashank, and Hans-Arno Jacobsen. "Analyzing Geospatial Distribution in Blockchains." arXiv preprint arXiv:2305.17771 (2023).
-   Nodetracker on Etherscan, https://etherscan.io/nodetracker, accessed 25th January 2024.
-   Censorship pics, https://censorship.pics/, accessed 25th January 2024.

## Credits

Thanks and credits to [Alberto Sonnino](https://github.com/asonnino) for the initial hotstuff and bullsharks benchmark.
