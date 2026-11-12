import json

from execution_costs.experiment import run


def test_experiment_is_reproducible_and_writes_its_report(tmp_path):
    first = run(tmp_path / "first")
    second = run(tmp_path / "second")

    assert first == second
    assert first["data_provenance"].startswith("synthetic")
    assert len(first["orders"]) == 5
    assert (tmp_path / "first" / "synthetic_cost_curve.png").stat().st_size > 0
    assert json.loads((tmp_path / "first" / "summary.json").read_text()) == first

    for order in first["orders"]:
        assert order["total_cost"] == (
            order["spread_cost"] + order["commission"] + order["market_impact"]
        )
        assert order["total_bps"] >= 0
