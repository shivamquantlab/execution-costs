"""Synthetic cost curve across order sizes with fixed model assumptions."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .model import estimate_trade_cost


def run(output_dir: Path) -> dict[str, object]:
    price, adv = 50.0, 2_000_000.0
    notionals = np.array([10_000, 25_000, 50_000, 100_000, 150_000], dtype=float)
    estimates = [
        estimate_trade_cost(
            notional / price,
            price,
            full_spread_bps=8.0,
            average_daily_dollar_volume=adv,
            commission_per_share=0.005,
            impact_coefficient_bps=20.0,
            max_participation=0.10,
        )
        for notional in notionals
    ]
    summary = {
        "data_provenance": "synthetic scenario inputs; no observed trades or market data",
        "cost_scope": "one-way estimated costs; no realized slippage or opportunity cost",
        "synthetic_reference_price": price,
        "synthetic_adv_dollars": adv,
        "assumed_full_spread_bps": 8.0,
        "assumed_commission_per_share": 0.005,
        "assumed_impact_coefficient_bps": 20.0,
        "maximum_adv_participation": 0.10,
        "orders": [
            {
                "notional": float(cost.notional),
                "spread_cost": cost.spread,
                "commission": cost.commission,
                "market_impact": cost.market_impact,
                "total_cost": cost.total,
                "total_bps": cost.total_bps,
            }
            for cost in estimates
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(notionals, [cost.spread for cost in estimates], marker="o", label="Half-spread")
    ax.plot(notionals, [cost.commission for cost in estimates], marker="o", label="Commission")
    ax.plot(notionals, [cost.market_impact for cost in estimates], marker="o", label="Square-root impact")
    ax.plot(notionals, [cost.total for cost in estimates], marker="o", lw=2, label="Total")
    ax.set(title="Illustrative synthetic order-cost curve", xlabel="Order notional (synthetic dollars)",
           ylabel="Estimated one-way cost")
    ax.legend(frameon=False, fontsize=8)
    ax.text(0.01, 0.98, "MODEL SCENARIO • not observed executions",
            transform=ax.transAxes, va="top", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "synthetic_cost_curve.png", dpi=150)
    plt.close(fig)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    run(args.output_dir)
    print(f"Wrote execution cost report to {args.output_dir}")


if __name__ == "__main__":
    main()
