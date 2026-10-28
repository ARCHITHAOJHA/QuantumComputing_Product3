# Hybrid Quantum Optimization System

A runnable educational application demonstrating hybrid quantum-classical optimization with QAOA for Max-Cut, Qiskit Aer ideal/noisy simulation, a simple readout-error mitigation experiment, and a Streamlit dashboard.

## Features

- QAOA parameterized quantum circuit and classical COBYLA optimizer
- Max-Cut objective on a small graph
- Exact classical brute-force optimum for validation
- Ideal and noisy Qiskit Aer execution
- Depolarizing gate noise and symmetric readout errors
- Illustrative readout mitigation using linear inversion, clipping, and renormalization
- Approximation ratios, objective degradation, runtime, outcome counts, CSV/JSON/Markdown reports
- Streamlit interface with configurable graph size, layers, shots, noise and seed

## Requirements

- Python 3.10–3.12 recommended
- pip and a virtual environment

Python 3.13/3.14 may have compatibility issues depending on the installed Qiskit/Aer wheels.

## Setup

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### macOS/Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Run a quick smoke test

```bash
python -c "from optimization.maxcut_problem import exact_maxcut; print(exact_maxcut(4, [(0,1),(1,2),(2,3),(3,0),(0,2)])[0])"
```

Optional unit tests:

```bash
pip install pytest
pytest -q
```

## How it works

1. The Max-Cut graph is encoded into a QAOA cost phase separator using `RZZ` gates and an X-mixer using `RX` gates.
2. A classical COBYLA optimizer searches the angles. The objective is the expected number of cut edges from simulator samples.
3. The optimized angles are evaluated with ideal and noisy Aer simulators.
4. A small-system readout mitigation estimate is computed by inverting an independent symmetric readout-error model.
5. Metrics and results are displayed and saved in `results/`.

## Important implementation notes

- QAOA results are stochastic; values may vary by seed and shot count.
- The optimizer objective is sampled, so small shot counts can make optimization noisy.
- Readout mitigation is a simplified demonstration. It can amplify statistical noise and does not mitigate gate errors.
- The exact classical solver is included only as a baseline for tiny graphs. This is not evidence of quantum advantage.
- No real quantum hardware is required. Hardware execution is an optional future extension.

## Suggested extensions

- Add VQE for a small Hamiltonian ground-state problem.
- Compare multiple noise levels and plot the degradation curve.
- Add measurement calibration based on experimentally measured calibration circuits.
- Add IBM Quantum hardware execution with a user-supplied account and current Qiskit Runtime APIs.
- Export a PDF report and include repeated trials with mean and standard deviation.
