import csv
from pathlib import Path


def save_csv(records: list, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "run", "L_uH", "C_uF", "esr_mOhm", "dcr_mOhm", "ron_mOhm",
            "vout_avg_V", "vout_pp_mV", "il_peak_A", "il_valley_A",
            "efficiency_pct", "passed",
        ])
        for r in records:
            s, x = r.sample, r.result
            writer.writerow([
                r.index, f"{s.inductance * 1e6:.4f}", f"{s.capacitance * 1e6:.4f}",
                f"{s.esr * 1e3:.3f}", f"{s.dcr * 1e3:.3f}", f"{s.ron * 1e3:.3f}",
                f"{x.vout_avg:.5f}", f"{x.vout_pp * 1e3:.3f}", f"{x.il_max:.4f}",
                f"{x.il_min:.4f}", f"{x.eff * 100:.3f}", int(r.passed),
            ])
    return path


def plot_results(records: list, criteria, path) -> Path:
    import matplotlib

    matplotlib.use("Agg")  # draw to a file, no window needed
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    ripple = [r.result.vout_pp * 1e3 for r in records]
    limit = criteria.vout_pp_max * 1e3

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

    ax1.hist(ripple, bins=20, color="tab:blue", edgecolor="white")
    ax1.axvline(limit, color="tab:red", linestyle="--", label=f"limit {limit:.0f} mV")
    ax1.set_xlabel("Output ripple, peak-to-peak (mV)")
    ax1.set_ylabel("Number of runs")
    ax1.set_title("Output ripple across part tolerances")
    ax1.legend()

    for ok, color, label in ((True, "tab:green", "pass"), (False, "tab:red", "fail")):
        subset = [r for r in records if r.passed == ok]
        ax2.scatter(
            [r.sample.inductance * r.sample.capacitance * 1e12 for r in subset],
            [r.result.vout_pp * 1e3 for r in subset],
            color=color, label=label, s=18,
        )
    ax2.axhline(limit, color="tab:red", linestyle="--")
    ax2.set_xlabel("Inductance x capacitance (uH x uF)")
    ax2.set_ylabel("Output ripple (mV)")
    ax2.set_title("Ripple falls as L x C grows")
    ax2.legend()

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path