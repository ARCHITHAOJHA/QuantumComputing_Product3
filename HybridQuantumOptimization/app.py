import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from optimization.maxcut_problem import DEFAULT_EDGES, exact_maxcut
from optimization.qaoa_circuit import run_qaoa_experiment
from evaluation.metrics import summarize_results
from evaluation.report import save_report

st.set_page_config(page_title="Hybrid Quantum Optimization", page_icon="⚛️", layout="wide")
st.title("⚛️ Hybrid Quantum Optimization System")
st.caption("QAOA for Max-Cut • Ideal vs. noisy Qiskit Aer simulation • Readout mitigation")

with st.sidebar:
    st.header("Experiment settings")
    n_nodes = st.slider("Number of nodes", 3, 6, 4)
    p_layers = st.slider("QAOA layers (p)", 1, 3, 1)
    shots = st.select_slider("Measurement shots", options=[256, 512, 1024, 2048], value=1024)
    maxiter = st.slider("Classical optimizer iterations", 10, 100, 40, step=10)
    gate_error = st.slider("Depolarizing gate error", 0.0, 0.05, 0.01, step=0.005)
    readout_error = st.slider("Readout error", 0.0, 0.15, 0.03, step=0.01)
    seed = st.number_input("Random seed", min_value=0, max_value=99999, value=7)

# Small connected graph with deterministic edges, adjustable node count.
edges = [(0,1),(1,2),(2,3),(3,0),(0,2),(2,4),(4,5),(5,0)]
edges = [(u,v) for u,v in edges if u < n_nodes and v < n_nodes]
if n_nodes == 3:
    edges = [(0,1),(1,2),(0,2)]
elif n_nodes == 4:
    edges = [(0,1),(1,2),(2,3),(3,0),(0,2)]

G = nx.Graph()
G.add_nodes_from(range(n_nodes))
G.add_edges_from(edges)
left, right = st.columns([1, 2])
with left:
    st.subheader("Optimization problem")
    st.write(f"**Nodes:** {n_nodes}  |  **Edges:** {len(edges)}")
    st.write("Find a binary partition of the graph that cuts the maximum number of edges.")
    fig, ax = plt.subplots()
    pos = nx.spring_layout(G, seed=seed)
    nx.draw_networkx(G, pos, ax=ax, node_color="#b7d7f0", node_size=800, font_weight="bold")
    ax.set_axis_off()
    st.pyplot(fig)
    plt.close(fig)

with right:
    st.subheader("Run experiment")
    st.write("The classical optimizer searches QAOA parameters. The same optimized parameters are evaluated with ideal and noisy simulators.")
    if st.button("Run QAOA experiment", type="primary", use_container_width=True):
        with st.spinner("Optimizing and evaluating circuits…"):
            try:
                result = run_qaoa_experiment(
                    n_nodes=n_nodes, edges=edges, p=p_layers, shots=shots,
                    maxiter=maxiter, gate_error=gate_error,
                    readout_error=readout_error, seed=int(seed)
                )
                exact_value, exact_strings = exact_maxcut(n_nodes, edges)
                metrics = summarize_results(result, exact_value)
                st.session_state["result"] = result
                st.session_state["metrics"] = metrics
                st.session_state["exact_value"] = exact_value
                st.session_state["exact_strings"] = exact_strings
                save_report(result, metrics, exact_value, edges)
            except Exception as exc:
                st.error(f"Experiment failed: {exc}")
                st.info("Check that dependencies installed successfully. See README.md for setup instructions.")

if "result" in st.session_state:
    result = st.session_state["result"]
    metrics = st.session_state["metrics"]
    st.divider()
    st.subheader("Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Exact optimum", f'{st.session_state["exact_value"]:.3f}')
    c2.metric("Ideal expected cut", f'{result["ideal"]["expected_cut"]:.3f}')
    c3.metric("Noisy expected cut", f'{result["noisy"]["expected_cut"]:.3f}')
    c4.metric("Noisy after mitigation", f'{result["mitigated"]["expected_cut"]:.3f}')
    st.caption("Mitigation uses a simple readout-calibration correction. It is illustrative and may not improve every run.")
    table = pd.DataFrame([
        {"Execution": "Ideal", **result["ideal"]},
        {"Execution": "Noisy", **result["noisy"]},
        {"Execution": "Noisy + readout mitigation", **result["mitigated"]},
    ])
    st.dataframe(table, use_container_width=True, hide_index=True)

    fig, ax = plt.subplots()
    labels = ["Ideal", "Noisy", "Mitigated"]
    vals = [result["ideal"]["expected_cut"], result["noisy"]["expected_cut"], result["mitigated"]["expected_cut"]]
    ax.bar(labels, vals)
    ax.axhline(st.session_state["exact_value"], linestyle="--", label="Exact optimum")
    ax.set_ylabel("Expected cut value")
    ax.set_title("Solution quality comparison")
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Most frequent measurement outcomes")
    outcomes = []
    for label in ["ideal", "noisy", "mitigated"]:
        counts = result[label]["counts"]
        for bitstring, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:8]:
            outcomes.append({"Execution": label, "Bitstring": bitstring, "Count": count, "Cut value": result[label]["cut_values"].get(bitstring, 0)})
    st.dataframe(pd.DataFrame(outcomes), use_container_width=True, hide_index=True)

    st.subheader("Performance metrics")
    st.dataframe(pd.DataFrame([metrics]), use_container_width=True, hide_index=True)
    st.download_button("Download metrics CSV", pd.DataFrame([metrics]).to_csv(index=False), "metrics.csv", "text/csv")
    st.download_button("Download raw experiment JSON", __import__("json").dumps(result, indent=2), "experiment_results.json", "application/json")
    st.info("All values are simulation results, not a guarantee of quantum advantage. For small graphs, exact classical search is a useful baseline.")
else:
    st.info("Choose settings in the sidebar and click **Run QAOA experiment** to start.")
