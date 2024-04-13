from re import findall

# open a file
with open('logs/node-0.log', 'r') as file:
    log = file.read()
    print(len(log))
    # tmp = findall(r'D\[(.*?)\].*committed block.*block=(.*).*', log)
    # tmp = findall(r'I\[(.*?)\].*received complete proposal block.*hash=([A-Fa-f0-9]+)', log)
    tmp = findall(r'D\[(.*?)\].*committed block.*block=.*([A-Fa-f0-9]+).*', log)
    print("length of committed block found: ", len(tmp))
    for match in tmp:
        timestamp, block_id = match
        print("Timestamp:", timestamp)
        print("Block ID:", block_id)
    # tmp = [(d, self._to_posix(t)) for t, d in tmp]
    # commits = self._merge_results([tmp])