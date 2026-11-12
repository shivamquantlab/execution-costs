"""Spread, commission, and participation-based square-root impact model."""

import math
from dataclasses import dataclass
from numbers import Real


def _finite_real(name: str, value: Real) -> float:
    """Return a finite float, rejecting booleans and non-numeric inputs."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite real number")
    return result


@dataclass(frozen=True)
class TradeCost:
    spread: float
    commission: float
    market_impact: float
    notional: float

    @property
    def total(self) -> float:
        return self.spread + self.commission + self.market_impact

    @property
    def total_bps(self) -> float:
        if self.notional == 0:
            return 0.0
        return self.total / self.notional * 10_000.0


def estimate_trade_cost(
    shares: float,
    price: float,
    *,
    full_spread_bps: float,
    average_daily_dollar_volume: float,
    commission_per_share: float = 0.0,
    impact_coefficient_bps: float = 20.0,
    max_participation: float = 0.10,
) -> TradeCost:
    """Estimate a symmetric, one-way cost in currency.

    Market impact uses coefficient_bps * sqrt(order_notional / ADV). The
    model is an illustrative scenario, not a calibrated fill predictor.
    """
    shares = _finite_real("shares", shares)
    price = _finite_real("price", price)
    full_spread_bps = _finite_real("full_spread_bps", full_spread_bps)
    average_daily_dollar_volume = _finite_real(
        "average_daily_dollar_volume", average_daily_dollar_volume
    )
    commission_per_share = _finite_real("commission_per_share", commission_per_share)
    impact_coefficient_bps = _finite_real("impact_coefficient_bps", impact_coefficient_bps)
    max_participation = _finite_real("max_participation", max_participation)

    if price <= 0 or average_daily_dollar_volume <= 0:
        raise ValueError("price and average daily dollar volume must be positive")
    if min(full_spread_bps, commission_per_share, impact_coefficient_bps) < 0:
        raise ValueError("cost parameters must be non-negative")
    if not 0 < max_participation <= 1:
        raise ValueError("max_participation must be in (0, 1]")
    notional = abs(shares) * price
    if not math.isfinite(notional):
        raise ValueError("order notional exceeds the finite numeric range")
    if shares != 0 and notional == 0:
        raise ValueError("order notional is too small for finite-precision arithmetic")
    participation = notional / average_daily_dollar_volume
    if participation > max_participation:
        raise ValueError("order exceeds the configured maximum ADV participation")
    spread_cost = notional * (full_spread_bps / 20_000.0)
    commission = abs(shares) * commission_per_share
    impact_bps = impact_coefficient_bps * math.sqrt(participation)
    impact_cost = notional * (impact_bps / 10_000.0)
    if notional == 0:
        return TradeCost(0.0, 0.0, 0.0, 0.0)
    if not all(math.isfinite(value) for value in (spread_cost, commission, impact_cost)):
        raise ValueError("estimated cost exceeds the finite numeric range")
    try:
        total = math.fsum((spread_cost, commission, impact_cost))
    except OverflowError as exc:
        raise ValueError("total estimated cost exceeds the finite numeric range") from exc
    if not math.isfinite(total) or not math.isfinite(total / notional * 10_000.0):
        raise ValueError("total estimated cost exceeds the finite numeric range")
    return TradeCost(spread_cost, commission, impact_cost, notional)
