import math

import pytest

from execution_costs import estimate_trade_cost


def _estimate(**overrides):
    inputs = {
        "shares": 100,
        "price": 10,
        "full_spread_bps": 10,
        "average_daily_dollar_volume": 100_000,
        "commission_per_share": 0.01,
        "impact_coefficient_bps": 20,
        "max_participation": 0.10,
    }
    inputs.update(overrides)
    return estimate_trade_cost(**inputs)


def test_cost_components_match_hand_calculation():
    cost = _estimate()
    assert cost.notional == pytest.approx(1_000)
    assert cost.spread == pytest.approx(0.5)
    assert cost.commission == pytest.approx(1.0)
    assert cost.market_impact == pytest.approx(0.2)
    assert cost.total == pytest.approx(1.7)
    assert cost.total_bps == pytest.approx(17.0)


def test_long_and_short_orders_have_symmetric_assumed_costs():
    assert _estimate(shares=100) == _estimate(shares=-100)


def test_zero_size_order_has_zero_cost_and_zero_bps():
    cost = _estimate(shares=0)
    assert cost.total == 0
    assert cost.total_bps == 0


def test_higher_adv_reduces_square_root_impact():
    thin = _estimate(
        full_spread_bps=0, commission_per_share=0, average_daily_dollar_volume=100_000
    )
    deep = _estimate(
        full_spread_bps=0, commission_per_share=0, average_daily_dollar_volume=400_000
    )
    assert deep.market_impact < thin.market_impact


def test_maximum_participation_boundary_is_inclusive():
    cost = _estimate(shares=1_000, price=10, average_daily_dollar_volume=100_000)
    assert cost.notional / 100_000 == pytest.approx(0.10)


def test_order_above_maximum_participation_is_rejected():
    with pytest.raises(ValueError, match="maximum ADV participation"):
        _estimate(shares=1_001, price=10, average_daily_dollar_volume=100_000)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("shares", math.nan),
        ("price", math.inf),
        ("full_spread_bps", -math.inf),
        ("average_daily_dollar_volume", math.nan),
        ("commission_per_share", math.inf),
        ("impact_coefficient_bps", math.nan),
        ("max_participation", math.inf),
    ],
)
def test_non_finite_inputs_are_rejected(field, value):
    with pytest.raises(ValueError, match=field):
        _estimate(**{field: value})


@pytest.mark.parametrize(("field", "value"), [("price", True), ("shares", "100")])
def test_non_real_inputs_raise_type_error(field, value):
    with pytest.raises(TypeError, match=field):
        _estimate(**{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("price", 0),
        ("average_daily_dollar_volume", 0),
        ("full_spread_bps", -1),
        ("commission_per_share", -0.01),
        ("impact_coefficient_bps", -1),
        ("max_participation", 0),
        ("max_participation", 1.01),
    ],
)
def test_domain_constraints_are_validated(field, value):
    with pytest.raises(ValueError):
        _estimate(**{field: value})


def test_tiny_order_that_underflows_notional_is_rejected():
    with pytest.raises(ValueError, match="too small"):
        _estimate(shares=1e-10, price=1e-320)


def test_cost_overflow_is_rejected_instead_of_returning_infinity():
    with pytest.raises(ValueError, match="finite numeric range"):
        _estimate(
            shares=1e308,
            price=1,
            full_spread_bps=1e308,
            average_daily_dollar_volume=1e308,
            commission_per_share=0,
            impact_coefficient_bps=0,
            max_participation=1,
        )
