import subprocess
import re
from collections import defaultdict

def run_ping(packet_size, ttl, target):
    """
    Runs:
      ping -f -l packet_size -n 1 -i ttl target
    Returns responding router IP or None.
    """

    cmd = [
        "ping",
        "-f",
        "-l", str(int(packet_size)),
        "-n", "1",
        "-i", str(ttl),
        str(target)
    ]

    try:
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = e.output  # ping returns non-zero on TTL expiry

    # Standard replies
    match = re.search(r"Reply from (\d+\.\d+\.\d+\.\d+)", output)
    if match:
        return match.group(1)

    # TTL Exceeded replies
    match = re.search(r"Reply from (\d+\.\d+\.\d+\.\d+): TTL expired in transit", output)
    if match:
        return match.group(1)

    return None


# ---------------------------
# TREE / GRAPH PRINTING LOGIC
# ---------------------------

def print_tree(graph, dest, root="(LOCAL)", target=None):
    print(root)

    visited = set()

    def label(node):
        return f"{node} (target)" if node == dest else node

    def dfs(node, prefix=""):
        if node in visited:
            print(prefix + "└── " , dest, "(target)")
            return

        visited.add(node)

        children = sorted(graph.get(node, []))

        # Target should always be a leaf
        if node == target:
            return

        for i, child in enumerate(children):
            connector = "└── " if i == len(children) - 1 else "├── "
            print(prefix + connector + label(child))
            new_prefix = prefix + ("    " if i == len(children) - 1 else "│   ")
            dfs(child, new_prefix)

    dfs(root)

# ---------------------------
# MAIN PROGRAM
# ---------------------------

def main():
    print("\n=== Network Exploration via Ping (TTL + Packet Size) ===")

    max_packet_size = int(input("Enter maximum packet size (bytes): "))
    max_ttl = int(input("Enter max hops: "))
    target = str(input("Enter target: "))

    # Graph structure: router -> set(next_routers)
    graph = defaultdict(set)

    print("\nScanning...\n")
    print(f"{'TTL':<5} {'PacketSize':<12} {'Responding Router':<20}")
    print("-" * 45)

    for size_step in range(1, 5):  # Your original loop: 4 size groups
        prev_router = None
        destination_router = None

        for ttl in range(1, max_ttl + 1):

            packet_size = size_step * (max_packet_size / 4)
            router = run_ping(packet_size, ttl, target)

            if router:
                print(f"{ttl:<5} {int(packet_size):<12} {router:<20}")

                # Record graph connection
                parent = prev_router if prev_router else "(LOCAL)"

                # Do not create loops, do not let target expand
                if router != parent and router != target:
                    graph[parent].add(router)
                elif router == target:
                    # Target is a leaf; only add incoming edge if parent != target
                    if parent != target:
                        graph[parent].add(router)


                # Stop when the same router appears twice in a row
                if router == prev_router:
                    destination_router = router
                    break

                prev_router = router

            else:
                print(f"{ttl:<5} {int(packet_size):<12} {'No Response'}")

        print()

    print("\nScan complete.\n")

    # ---------------------------
    # PRINT THE NETWORK TREE
    # ---------------------------
    print("\n=== Network Path Tree ===\n")
    print_tree(graph, destination_router, root="(LOCAL)", target=None)
    print()
    print()
    print()


if __name__ == "__main__":
    main()
