def summarize_results(result, exact_optimum):
    ideal = result["ideal"]["expected_cut"]
    noisy = result["noisy"]["expected_cut"]
    mitigated = result["mitigated"]["expected_cut"]
    denom = exact_optimum if exact_optimum else 1
    return {
        "exact_optimum": float(exact_optimum),
        "ideal_expected_cut": round(ideal, 6),
        "noisy_expected_cut": round(noisy, 6),
        "mitigated_expected_cut": round(mitigated, 6),
        "ideal_approximation_ratio": round(ideal / denom, 6),
        "noisy_approximation_ratio": round(noisy / denom, 6),
        "mitigated_approximation_ratio": round(mitigated / denom, 6),
        "noise_degradation_ideal_minus_noisy": round(ideal - noisy, 6),
        "mitigation_change_noisy_to_mitigated": round(mitigated - noisy, 6),
        "runtime_seconds": round(result["runtime_seconds"], 4),
        "optimizer_iterations": result["optimizer"]["iterations"],
    }
