# GeoDec: Enhancing Blockchain Resilience through Geospatial Validator Distribution

GeoDec aims to address the geographic concentration of validator nodes in existing blockchain networks, particularly in the context of PoS consensus mechanisms. The project involves the development of an emulator to analyze geospatial distribution, the design of a geospatial-aware proposer selection mechanism, and deploying the revised protocol for evaluation.


## Get Started
You need to have hotstuff and cometbft on the main machine. \
This is required to create the node config files needed send it to instances.

For cometbft you can use the binary (light weight and easy) \
For hotstuff you need to clone the repo and install cargo rust\
The node config is same for hotstuff and bullshark

Clone the GeoDec repo and install the requirements
``` bash
git clone https://github.com/GeoDecConsensus/geodec.git
cd geodec
pip install -r requirements.txt
```

Clone hotstuff
``` bash
git clone https://github.com/GeoDecConsensus/hotstuff.git
```
Clone cometbft binary
``` bash
curl -LO  https://github.com/cometbft/cometbft/releases/download/v0.38.6/cometbft_0.38.6_linux_amd64.tar.gz
mkdir cometbft-dir
tar xvf cometbft_0.38.6_linux_amd64.tar.gz -C cometbft-dir
mv cometbft-dir/cometbft ./
rm -r cometbft_0.38.6_linux_amd64.tar.gz cometbft-dir
```

Install rust (non-interactive)
``` bash
'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y',
'source $HOME/.cargo/env',
'rustup default stable',
```

## Progress

**Emulator Development**
- [x] Develop HotStuff emulator
- [x] Extend emulator for Tendermint consensus mechanisms (like CometBFT)
- [x] Extend emulator for BullShark consensus mechanism
- [ ] Implement and improvise a modular and extensible code structure
    - [ ] Improve the cometbft benchmark by making changes in the forked repo
    - [ ] Improve code structure and documentation
- [ ] Get feedback from the community
- [ ] Improve emulator based on the feedback

### Vision
Success for GeoDec entails advancing geospatial decentralization in blockchain validator networks. The desired impact includes the development of a widely-used open-source emulator, an effective mechanism for geographically decentralized block proposers, and influential academic research. The goal is to set new standards for blockchain networks globally.

### References
- Motepalli, Shashank, and Hans-Arno Jacobsen. "Analyzing Geospatial Distribution in Blockchains." arXiv preprint arXiv:2305.17771 (2023).
- Nodetracker on Etherscan, https://etherscan.io/nodetracker, accessed 25th January 2024.
- Censorship pics, https://censorship.pics/, accessed 25th January 2024.

### Credits
Thanks to [Alberto Sonnino](https://github.com/asonnino) for the initial hotstuff benchmark.
