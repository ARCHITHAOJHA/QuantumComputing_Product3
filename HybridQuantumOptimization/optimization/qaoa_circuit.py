"""QAOA Max-Cut experiment using Qiskit and Qiskit Aer.

The circuit uses a standard cost phase separator exp(-i gamma H_C) and X-mixer.
The measured objective is the number of cut edges. Qiskit's displayed bitstrings
are reversed into node order before evaluating the graph objective.
"""
import time
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError
from optimization.maxcut_problem import cut_value

def build_qaoa_circuit(n_nodes, edges, gammas, betas, measure=True):
    qc = QuantumCircuit(n_nodes)
    qc.h(range(n_nodes))
    for gamma, beta in zip(gammas, betas):
        # For each edge, exp(-i gamma * (1 - ZiZj)/2) differs from
        # RZZ(gamma) only by a global phase, so RZZ(gamma) is sufficient.
        for u, v in edges:
            qc.rzz(float(gamma), u, v)
        for q in range(n_nodes):
            qc.rx(2.0 * float(beta), q)
    if measure:
        qc.measure_all()
    return qc

def make_noise_model(n_nodes, gate_error, readout_error):
    model = NoiseModel()
    if gate_error > 0:
        one_qubit = depolarizing_error(gate_error, 1)
        two_qubit = depolarizing_error(gate_error, 2)
        model.add_all_qubit_quantum_error(one_qubit, ["h", "rx"])
        model.add_all_qubit_quantum_error(two_qubit, ["rzz"])
    if readout_error > 0:
        p = float(readout_error)
        ro = ReadoutError([[1-p, p], [p, 1-p]])
        model.add_all_qubit_readout_error(ro)
    return model

def _bitstring_to_node_order(qiskit_bitstring, n_nodes):
    return qiskit_bitstring.replace(" ", "")[::-1][-n_nodes:]

def _counts_and_values(counts, n_nodes, edges):
    normalized = {}
    for raw, count in counts.items():
        s = _bitstring_to_node_order(raw, n_nodes)
        normalized[s] = normalized.get(s, 0) + int(count)
    cut_values = {s: int(cut_value(s, edges)) for s in normalized}
    shots = sum(normalized.values()) or 1
    expected = sum(cut_values[s] * count for s, count in normalized.items()) / shots
    return {"counts": normalized, "cut_values": cut_values, "expected_cut": float(expected),
            "best_observed_cut": int(max(cut_values.values(), default=0))}

def _execute(n_nodes, edges, params, p, shots, seed, noise_model=None):
    gammas = params[:p]
    betas = params[p:]
    circuit = build_qaoa_circuit(n_nodes, edges, gammas, betas, measure=True)
    backend = AerSimulator(noise_model=noise_model) if noise_model else AerSimulator()
    compiled = transpile(circuit, backend, seed_transpiler=seed, optimization_level=1)
    counts = backend.run(compiled, shots=shots, seed_simulator=seed).result().get_counts()
    return _counts_and_values(counts, n_nodes, edges)

def run_qaoa_experiment(n_nodes, edges, p=1, shots=1024, maxiter=40,
                        gate_error=0.01, readout_error=0.03, seed=7):
    """Optimize parameters on an ideal simulator, then compare ideal/noisy/mitigated."""
    start = time.perf_counter()
    rng = np.random.default_rng(seed)
    initial = np.concatenate([rng.uniform(0, np.pi, p), rng.uniform(0, np.pi/2, p)])
    history = []

    def objective(params):
        result = _execute(n_nodes, edges, params, p, max(256, min(shots, 512)), seed)
        history.append(result["expected_cut"])
        return -result["expected_cut"]

    opt = minimize(objective, initial, method="COBYLA",
                   options={"maxiter": int(maxiter), "rhobeg": 0.5})
    params = opt.x
    ideal = _execute(n_nodes, edges, params, p, shots, seed)
    noise = make_noise_model(n_nodes, gate_error, readout_error)
    noisy = _execute(n_nodes, edges, params, p, shots, seed + 1, noise)
    # Lightweight readout correction: invert the independent symmetric readout channel
    # on the observed probability distribution, clip negative estimates, then normalize.
    mitigated = mitigate_symmetric_readout(noisy["counts"], n_nodes, readout_error, edges)
    elapsed = time.perf_counter() - start
    return {
        "configuration": {"n_nodes": n_nodes, "edges": [list(e) for e in edges],
                          "p": p, "shots": shots, "maxiter": maxiter,
                          "gate_error": gate_error, "readout_error": readout_error, "seed": seed},
        "parameters": [float(x) for x in params],
        "optimizer": {"success": bool(opt.success), "message": str(opt.message),
                      "iterations": int(getattr(opt, "nfev", len(history))),
                      "objective_history": [float(x) for x in history]},
        "ideal": ideal, "noisy": noisy, "mitigated": mitigated,
        "runtime_seconds": float(elapsed)
    }

def mitigate_symmetric_readout(counts, n_nodes, readout_error, edges):
    """Approximate full-distribution readout correction for small n (up to 6 qubits)."""
    if readout_error <= 0 or n_nodes > 8:
        return {**_counts_and_values(counts, n_nodes, edges), "mitigation": "not needed or size limit"}
    keys = [format(i, f"0{n_nodes}b") for i in range(2**n_nodes)]
    total = sum(counts.values()) or 1
    observed = np.array([counts.get(k, 0) / total for k in keys], dtype=float)
    # Tensor-product confusion matrix. Rows are observed strings; columns are true strings.
    one = np.array([[1-readout_error, readout_error],
                    [readout_error, 1-readout_error]], dtype=float)
    matrix = np.array([[1.0]])
    for _ in range(n_nodes):
        matrix = np.kron(matrix, one)
    try:
        corrected = np.linalg.solve(matrix, observed)
    except np.linalg.LinAlgError:
        corrected = observed
    corrected = np.clip(corrected, 0, None)
    if corrected.sum() == 0:
        corrected = observed
    corrected /= corrected.sum()
    pseudo_counts = {k: float(corrected[i] * total) for i, k in enumerate(keys) if corrected[i] > 0}
    cut_values = {k: int(cut_value(k, edges)) for k in pseudo_counts}
    expected = sum(cut_values[k] * v for k, v in pseudo_counts.items()) / sum(pseudo_counts.values())
    return {"counts": pseudo_counts, "cut_values": cut_values, "expected_cut": float(expected),
            "best_observed_cut": int(max(cut_values.values(), default=0)),
            "mitigation": "linear inversion of symmetric readout channel; clipped and renormalized"}
