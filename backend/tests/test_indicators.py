"""燈號與綜合分數計算的單元測試（以 mock 資料 + 合成情境）。"""
from __future__ import annotations

import numpy as np

from app.config import settings
from app.data import MarketData, Series
from app.data import mock_provider
from app.indicators import composite, margin_institutional, per_deviation, volatility
from app.indicators.utils import clamp, percentile_rank, zscore
from app.services import risk_service


def _const_series(dates, value):
    return Series(dates, [value] * len(dates))


def _make_data(margin, inst, per, vix) -> MarketData:
    n = len(margin)
    dates = [f"2026-01-{(i % 28) + 1:02d}" for i in range(n)]
    return MarketData(
        margin=Series(dates, margin),
        institutional=Series(dates, inst),
        per=Series(dates, per),
        vix=Series(dates, vix),
        index=Series(dates, [18000.0 + i for i in range(n)]),
        source="mock",
    )


# ── utils ────────────────────────────────────────────────────────────────
def test_percentile_rank_bounds():
    hist = np.arange(100, dtype=float)
    assert percentile_rank(hist, 200) == 100.0
    assert percentile_rank(hist, -5) == 0.0


def test_zscore_zero_std():
    assert zscore(np.array([5.0, 5.0, 5.0]), 5.0) == 0.0


def test_clamp():
    assert clamp(150) == 100.0
    assert clamp(-3) == 0.0


# ── 前兆1：融資×法人背離 ───────────────────────────────────────────────
def test_margin_red_when_high_and_selling():
    w = settings.windows
    n = 120
    margin = list(np.linspace(1000, 2000, n))  # 持續創新高，末值為 60 日最高
    inst = [10.0] * (n - 12) + [-50.0] * 12     # 近 10 日明顯淨賣
    data = _make_data(margin, inst, [15.0] * n, [20.0] * n)
    sig = margin_institutional.evaluate(data, w)
    assert sig.margin_high is True
    assert sig.inst_selling is True
    assert sig.light == "red"


def test_margin_green_when_calm():
    w = settings.windows
    n = 120
    margin = list(2000 - np.linspace(0, 500, n))  # 持續下降，非新高
    inst = [30.0] * n                              # 持續淨買
    data = _make_data(margin, inst, [15.0] * n, [20.0] * n)
    sig = margin_institutional.evaluate(data, w)
    assert sig.margin_high is False
    assert sig.inst_selling is False
    assert sig.light == "green"


# ── 前兆2：本益比偏離 ──────────────────────────────────────────────────
def test_per_red_when_extreme():
    w, t = settings.windows, settings.thresholds
    base = list(np.full(300, 15.0) + np.random.default_rng(1).normal(0, 0.5, 300))
    per = base + [40.0]  # 末值極端偏高
    data = _make_data([1000.0] * len(per), [0.0] * len(per), per, [20.0] * len(per))
    sig = per_deviation.evaluate(data, w, t)
    assert sig.light == "red"
    assert sig.sigma > t.per_sigma_red


# ── 前兆3：波動率極低（反直覺）────────────────────────────────────────
def test_volatility_red_when_low():
    w, t = settings.windows, settings.thresholds
    rng = np.random.default_rng(2)
    vix = list(25 + rng.normal(0, 3, 300)) + [5.0]  # 末值落在最低區間
    data = _make_data([1000.0] * len(vix), [0.0] * len(vix), [15.0] * len(vix), vix)
    sig = volatility.evaluate(data, w, t)
    assert sig.light == "red"
    assert sig.score > 80  # 低波動 → 高子分數


# ── 模組B：綜合分數 ───────────────────────────────────────────────────
def test_composite_weighting_and_light():
    comp = composite.evaluate(mock_provider.generate(), settings, 90.0, 90.0, 90.0)
    assert comp.light == "red"
    assert comp.score >= settings.thresholds.composite_red
    assert "觀測" in comp.hint


def test_composite_trend_length():
    data = mock_provider.generate()
    comp = composite.evaluate(data, settings, 50.0, 50.0, 50.0)
    assert len(comp.trend) == settings.windows.composite_trend_days
    assert all(0 <= p.score <= 100 for p in comp.trend)


# ── 端到端：service.compute 以 mock 跑通 ──────────────────────────────
def test_compute_end_to_end_mock():
    result = risk_service.compute(settings)
    assert result.data_source == "mock"
    assert 0 <= result.composite.score <= 100
    assert result.signals.volatility.is_mock is True
    for light in (
        result.signals.margin_institutional.light,
        result.signals.per.light,
        result.signals.volatility.light,
        result.composite.light,
    ):
        assert light in ("green", "yellow", "red")


# ── Phase 3：美股對照指標 ──────────────────────────────────────────────
def test_us_reference_mock():
    from app.data import mock_provider
    from app.indicators import us_reference

    ref = mock_provider.generate_us_reference()
    out = us_reference.evaluate(ref, settings.windows, settings.thresholds)
    assert out.is_mock is True
    assert len(out.indicators) == 3
    names = {i.name for i in out.indicators}
    assert {"美股 VIX", "Shiller CAPE", "巴菲特指標"} == names
    for ind in out.indicators:
        assert ind.light in ("green", "yellow", "red")
        assert 0 <= ind.pctile <= 100
        assert len(ind.series) > 0


# ── Phase 3：歷史回測 ─────────────────────────────────────────────────
def test_backtest_mock():
    from app.services import backtest

    out = backtest.run(settings, horizon=20)
    assert out.is_mock is True
    assert out.horizon == 20
    assert len(out.points) > 50
    assert sum(b.count for b in out.buckets) == len(out.points)
    assert -1.0 <= out.correlation <= 1.0
    # 每個 bucket 的 light 應唯一且涵蓋三色
    assert {b.light for b in out.buckets} == {"green", "yellow", "red"}


def test_backtest_horizon_bounds():
    from app.services import backtest

    short = backtest.run(settings, horizon=10)
    long = backtest.run(settings, horizon=60)
    # 前瞻越長，可用樣本越少
    assert len(long.points) <= len(short.points)


# ── Phase 3：每週摘要文案 ─────────────────────────────────────────────
def test_weekly_summary_text():
    from app.services import alerts

    result = risk_service.compute(settings)
    text = alerts.build_weekly_summary(result)
    assert "本週風險摘要" in text
    assert "綜合風險分數" in text
