"""模組E 選股策略單元測試（全程 mock，不需 token / 網路）。"""
from __future__ import annotations

from app.config import Settings, StrategyConfig
from app.data.stock_provider import generate_mock_snapshots, get_stock_snapshots
from app.data.universe import Stock, full_universe
from app.indicators import stock_strategy
from app.services import picks_service


def _snap_for_regime(regime: int):
    """挑一個 ticker hash % 4 == regime 的 mock 快照。"""
    i = 0
    while True:
        s = Stock(f"T{i}", f"name{i}", "tw")
        if abs(hash(s.ticker)) % 4 == regime:
            return generate_mock_snapshots([s])[0]
        i += 1


def test_scores_in_range():
    cfg = StrategyConfig()
    for snap in generate_mock_snapshots(full_universe()):
        pick = stock_strategy.evaluate(snap, "green", cfg)
        for v in (pick.score, pick.scores.value, pick.scores.momentum, pick.scores.dividend):
            assert 0 <= v <= 100
        assert pick.risk_light in ("green", "yellow", "red")
        assert pick.top_style in ("value", "momentum", "dividend")


def test_value_regime_scores_high_on_value():
    pick = stock_strategy.evaluate(_snap_for_regime(0), "green", StrategyConfig())
    # 價值股（超賣、低 PER）價值子分數應高於動能子分數
    assert pick.scores.value > pick.scores.momentum


def test_momentum_regime_scores_high_on_momentum():
    pick = stock_strategy.evaluate(_snap_for_regime(1), "green", StrategyConfig())
    assert pick.scores.momentum > pick.scores.value


def test_overheated_regime_flags_risk():
    pick = stock_strategy.evaluate(_snap_for_regime(3), "green", StrategyConfig())
    # 過熱股（RSI 高、PER 很高）風險燈不應為綠
    assert pick.risk_light in ("yellow", "red")


def test_market_red_raises_risk():
    snap = _snap_for_regime(1)
    green = stock_strategy.evaluate(snap, "green", StrategyConfig())
    red = stock_strategy.evaluate(snap, "red", StrategyConfig())
    # 大盤紅燈時，rationale 應加註系統性風險提醒
    assert "大盤" in red.rationale
    assert "大盤" not in green.rationale


def test_weights_shift_ranking():
    snaps = generate_mock_snapshots(full_universe())
    div_heavy = StrategyConfig(w_value=0, w_momentum=0, w_dividend=1)
    mom_heavy = StrategyConfig(w_value=0, w_momentum=1, w_dividend=0)
    top_div = max(snaps, key=lambda s: stock_strategy.evaluate(s, "green", div_heavy).score)
    top_mom = max(snaps, key=lambda s: stock_strategy.evaluate(s, "green", mom_heavy).score)
    # 不同權重應選出不同主導風格的標的
    p_div = stock_strategy.evaluate(top_div, "green", div_heavy)
    p_mom = stock_strategy.evaluate(top_mom, "green", mom_heavy)
    assert p_div.top_style == "dividend"
    assert p_mom.top_style == "momentum"


def test_picks_service_compute_mock():
    settings = Settings(data_source="mock")
    snaps, source = get_stock_snapshots(settings)
    assert source == "mock"
    assert len(snaps) == len(full_universe())

    result = picks_service.compute(settings)
    assert len(result.top) == settings.strategy.top_n
    # top 依分數遞減
    assert all(
        result.top[i].score >= result.top[i + 1].score
        for i in range(len(result.top) - 1)
    )
    # universe 涵蓋全宇宙，供追蹤清單查詢
    assert len(result.universe) == len(full_universe())
    assert all(p.risk_light == "red" for p in result.warnings)
