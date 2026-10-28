import json
import os
import pandas as pd

def save_report(result, metrics, exact_optimum, edges, output_dir="results"):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "experiment_results.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    with open(os.path.join(output_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    pd.DataFrame([metrics]).to_csv(os.path.join(output_dir, "metrics.csv"), index=False)
    with open(os.path.join(output_dir, "experiment_report.md"), "w", encoding="utf-8") as f:
        f.write("# Hybrid Quantum Optimization Experiment Report\n\n")
        f.write(f"- Exact classical optimum: **{exact_optimum}**\n")
        f.write(f"- Graph edges: `{edges}`\n\n")
        f.write("## Metrics\n\n")
        for key, value in metrics.items():
            f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
        f.write("\n## Notes\n\n")
        f.write("This is a small-scale simulator experiment. Results are stochastic and do not establish quantum advantage. ")
        f.write("Readout mitigation uses a simplified independent symmetric-error model.\n")
