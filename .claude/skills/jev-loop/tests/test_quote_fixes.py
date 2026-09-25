"""Regression tests for two bugs found installing the published prompt:
resting bids piling up past the position cap when the account is flat,
and an Avellaneda-Stoikov spread fixed in dollars instead of scaled to
price."""

import time

import pytest

from jevloop import loop, risk
from jevloop.assets import resolve_symbol
from jevloop.execution.alpaca import AlpacaAPIError
from jevloop.limits import Limits
from jevloop.policy import QUOTE_WIDE, Action
from jevloop.pricing import quote_prices
from jevloop.state import InventoryState

BTC = resolve_symbol("BTC/USD")


class CashPaper:
    """A cash account: a sell with nothing held is rejected, like Alpaca."""

    order_prefix = "jevloop-test-"

    def __init__(self, held=0.0):
        self._order_seq = 0
        self.held = held
        self.open = []

    def submit_limit_order(self, side, qty, px):
        if side == "sell" and qty > self.held + 1e-12:
            raise AlpacaAPIError(403, "insufficient balance for BTC")
        self._order_seq += 1
        self.open.append((side, qty, px))
        return {"client_order_id": f"{self.order_prefix}{self._order_seq}"}

    def submit_market_order(self, side, qty):
        self._order_seq += 1
        return {"client_order_id": f"{self.order_prefix}{self._order_seq}"}

    def cancel_own_orders(self):
        n = len(self.open)
        self.open.clear()
        return n

    def get_position_qty(self):
        return self.held


def _tick(monkeypatch, alp, inv, rq, rc, leg=None, dry=False, mid=85_000.0):
    monkeypatch.setattr(risk, "check", lambda *a, **k: risk.RiskVerdict(ok=True))
    return loop._execute_action(
        alpaca=alp,
        spec=BTC,
        action=Action(QUOTE_WIDE, "test", direction_leg=leg),
        bid_px=mid - 1,
        ask_px=mid + 1,
        mid=mid,
        quote_notional=20.0,
        directional_notional=20.0,
        snapshot={},
        limits=Limits(),
        inv=inv,
        api_error_streak=0,
        decision_latency_ms=100.0,
        resting_quotes=rq,
        rest_counter=rc,
        now=time.time(),
        dry=dry,
        expected_px={},
    )


def test_flat_account_never_piles_up_bids(monkeypatch):
    alp, inv, rq, rc = CashPaper(), InventoryState(), None, 0
    for _ in range(30):
        _, fill_txt, _, _, rq, rc = _tick(monkeypatch, alp, inv, rq, rc)
    buys = [o for o in alp.open if o[0] == "buy"]
    assert len(buys) == 1 and not [o for o in alp.open if o[0] == "sell"]
    assert inv.orders_rejected == 0  # no guaranteed-to-fail sell was sent


def test_placed_side_is_tracked_even_when_the_next_side_is_rejected(monkeypatch):
    alp = CashPaper(held=0.0)
    inv = InventoryState(inventory=0.00015)  # the run thinks it holds $12.75...
    line, _, _, _, rq, _ = _tick(monkeypatch, alp, inv, None, 0)
    assert "order error" in line  # ...the account says no
    assert rq is not None and rq["buy_usd"] > 0  # the bid it did place is remembered
    _tick(monkeypatch, alp, inv, rq, 99)  # next re-quote cancels it first
    assert len([o for o in alp.open if o[0] == "buy"]) == 1


def test_bid_is_skipped_at_the_position_cap(monkeypatch):
    alp = CashPaper(held=0.0005)
    inv = InventoryState(inventory=0.0005)  # $42.50 held, cap is $50
    _, txt, _, _, rq, _ = _tick(monkeypatch, alp, inv, None, 0)
    assert "bid skipped" in txt
    assert [o[0] for o in alp.open] == ["sell"]


def test_ask_only_offers_what_is_held(monkeypatch):
    alp = CashPaper(held=0.0002)
    inv = InventoryState(inventory=0.0002)  # $17 held, quote target $20
    _tick(monkeypatch, alp, inv, None, 0)
    asks = [o for o in alp.open if o[0] == "sell"]
    assert asks and asks[0][1] == pytest.approx(0.0002)


def test_buy_leg_counts_resting_bids_against_the_cap(monkeypatch):
    alp = CashPaper()
    inv = InventoryState(inventory=0.0002)  # $17 held
    rq = {"bid": 84_999.0, "buy_usd": 20.0}  # plus a $20 bid resting
    _, txt, *_ = _tick(monkeypatch, alp, inv, rq, 0, leg="up")
    assert "buy leg skipped" in txt


def test_dry_run_reports_the_same_sides(monkeypatch):
    alp = CashPaper()
    _, txt, *_ = _tick(monkeypatch, alp, InventoryState(), None, 0, dry=True)
    assert txt.startswith("dry: would quote buy") and "ask skipped" in txt
    assert alp.open == []


# -- A-S in basis points of mid -----------------------------------------------


def _width_bps(mid, **kw):
    L = Limits()
    b, a = quote_prices(
        mid=mid,
        inventory_frac=kw.get("q", 0.0),
        sigma=kw.get("sigma", 5e-4),
        gamma=L.as_gamma,
        kappa=L.as_kappa,
        time_left_s=L.as_horizon_s,
    )
    return (a - b) / mid * 1e4, (b + a) / 2


def test_spread_is_the_same_in_bps_at_any_price():
    w_coin, _ = _width_bps(85_000.0)
    w_stock, _ = _width_bps(30.0)
    assert w_coin == pytest.approx(w_stock)
    assert 2.0 < w_coin < 20.0  # a few bps, not 0.3 or 860


def test_long_inventory_skews_quotes_down_and_vol_widens_them():
    _, centre_flat = _width_bps(100.0)
    _, centre_long = _width_bps(100.0, q=1.0)
    assert centre_long < centre_flat
    assert _width_bps(100.0, sigma=2e-3)[0] > _width_bps(100.0, sigma=5e-4)[0]


def test_quotes_round_outward_to_the_tick_and_never_touch_mid():
    b, a = quote_prices(
        mid=30.005, inventory_frac=0, sigma=1e-5, gamma=0.1, kappa=1.5,
        time_left_s=60, tick_size=0.01,
    )
    assert b <= 30.005 - 0.01 and a >= 30.005 + 0.01
    assert round(b, 2) == pytest.approx(b) and round(a, 2) == pytest.approx(a)
