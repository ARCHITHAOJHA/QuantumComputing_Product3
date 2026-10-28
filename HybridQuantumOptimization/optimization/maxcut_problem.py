from itertools import product

DEFAULT_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]

def cut_value(bitstring, edges):
    """Return number of edges whose endpoints are assigned to different partitions."""
    bits = [int(ch) for ch in bitstring]
    return sum(bits[u] != bits[v] for u, v in edges)

def exact_maxcut(n_nodes, edges):
    """Brute-force exact optimum for small graphs; returns optimum and optimal bitstrings."""
    best = -1
    solutions = []
    for bits in product([0, 1], repeat=n_nodes):
        string = "".join(map(str, bits))
        value = cut_value(string, edges)
        if value > best:
            best, solutions = value, [string]
        elif value == best:
            solutions.append(string)
    return best, solutions
