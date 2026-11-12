# Execution Costs

An independently installable Python project for transparent, assumption-driven estimates of one-way trading costs. It separates quoted half-spread, per-share commission, and stylized participation-based market impact.

## Research question

How do order size and explicit spread, commission, and impact assumptions change estimated one-way execution cost?

## Methodology

For signed order size in shares \(q\), reference price \(p\), full quoted spread \(s\) in basis points, average daily dollar volume \(D\), commission \(f\) per share, and impact coefficient \(\eta\) in basis points, the implementation uses absolute order notional \(N=|q|p\):

\[
C_{spread}=N\frac{s/2}{10{,}000},\qquad
C_{commission}=|q|f,
\]

\[
i_{impact}=\eta\sqrt{N/D},\qquad
C_{impact}=N\frac{i_{impact}}{10{,}000}.
\]

The reported total is the sum of these components, with basis points computed as \(10{,}000 C_{total}/N\). The order is rejected when \(N/D\) exceeds the configured participation ceiling (10% by default); the model does not extrapolate beyond that limit. Costs are symmetric for buys and sells and are modeled one way.

## Synthetic experiment and provenance

The checked-in report is generated from an explicit synthetic scenario: reference price 50, dollar ADV 2,000,000, full spread 8 bp, commission 0.005 per share, impact coefficient 20 bp, and maximum participation 10%. These are illustrative inputs, not market observations. The experiment is deterministic and does not use random numbers, external data, paid APIs, or credentials.

The [summary report](reports/summary.json) records each input and cost component. The [chart](reports/synthetic_cost_curve.png) plots the same five notionals and model outputs recorded in that summary.

## Installation and usage

Requires Python 3.11–3.13. With [uv](https://docs.astral.sh/uv/), install the locked runtime and test dependencies and regenerate the report:

```bash
uv sync --locked --extra test
uv run --locked execution-cost-demo
```

The command writes `reports/summary.json` and `reports/synthetic_cost_curve.png`. To use the model directly:

```python
from execution_costs import estimate_trade_cost

estimate = estimate_trade_cost(
    shares=1_000,
    price=50.0,
    full_spread_bps=8.0,
    average_daily_dollar_volume=2_000_000.0,
    commission_per_share=0.005,
    impact_coefficient_bps=20.0,
)
print(estimate.total, estimate.total_bps)
```

## Validation

```bash
uv run --locked pytest
uv run --locked ruff check src tests
```

Tests compare the formulas with a hand calculation, exercise input and participation boundaries, reject non-finite results, and regenerate the synthetic report twice to check reproducibility.

## Assumptions and limitations

- The square-root impact form is stylized; its coefficient is not empirically calibrated and does not predict actual fills.
- The model omits intraday volume profiles, volatility, order type, queue position, venue fees or rebates, market state, and nonlinear interactions among costs.
- It reports modeled one-way cost only. It excludes realized slippage, opportunity cost, financing, taxes, and all portfolio returns.
- The participation limit is a safety bound for this scenario model, not a liquidity guarantee.

**Research disclaimer:** All trading cost examples use synthetic assumptions. They do not use real market data, represent executed trades, or provide evidence of real investment returns. This project is educational research, not investment advice.
