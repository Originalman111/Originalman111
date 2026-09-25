"""Avellaneda-Stoikov reservation price and half spread.

Fifty-year-old market-making maths. Stays in code. No model call, ever.
Jev never sees this file's output as a question. It only answers whether
the state is worth quoting into at all (policy.py). This file answers
where to quote.

    reservation r = mid - inventory * gamma * sigma^2 * (T - t)
    half spread   = gamma * sigma^2 * (T - t) + (2 / gamma) * ln(1 + gamma / kappa)

Units. Textbook A-S works in price units: sigma in dollars, kappa in
1/dollars, inventory in shares. Fed a dimensionless sigma (the log-return
volatility state.py computes) and a fixed kappa, that gives a spread fixed
in dollars: 0.3 bps wide on an $85,000 coin, 860 bps wide on a $30 stock.
quote_prices() therefore runs the same formulas in basis points of mid:
sigma is converted to bps per step, kappa is read as order-arrival decay
per bp, and inventory is the position's share of the dollar position cap
(-1..1). The result is multiplied back by mid, so the same parameters mean
the same thing on any asset at any price.
"""

from __future__ import annotations

import math

VOL_STEP_S = 60.0  # state.py samples realised volatility on a one-minute grid


def reservation_price(
    mid: float,
    inventory: float,
    gamma: float,
    sigma: float,
    time_left_s: float,
) -> float:
    """Reservation price: mid, skewed away from the side that grows inventory.

    A positive inventory (long) pulls the reservation price below mid so the
    quoting logic favours selling; a negative inventory pulls it above mid.
    """
    return mid - inventory * gamma * (sigma**2) * time_left_s


def half_spread(gamma: float, sigma: float, time_left_s: float, kappa: float) -> float:
    """Half the total quoted spread around the reservation price."""
    inventory_term = gamma * (sigma**2) * time_left_s
    liquidity_term = (2.0 / gamma) * math.log1p(gamma / kappa)
    return inventory_term + liquidity_term


def quote_prices(
    mid: float,
    inventory_frac: float,
    sigma: float,
    gamma: float,
    kappa: float,
    time_left_s: float,
    tick_size: float = 0.0,
) -> tuple[float, float]:
    """Returns (bid, ask) around the reservation price, scaled to mid.

    `inventory_frac` is position value / max_position_usd, signed.
    `sigma` is the per-minute log-return volatility from state.py.
    With a tick size, the bid rounds down and the ask rounds up, and each
    stays at least one tick off mid so a quote never crosses it."""
    sigma_bps = sigma * 10_000
    steps = time_left_s / VOL_STEP_S
    r_bps = reservation_price(0.0, inventory_frac, gamma, sigma_bps, steps)
    h_bps = half_spread(gamma, sigma_bps, steps, kappa)
    bid = mid * (1 + (r_bps - h_bps) / 10_000)
    ask = mid * (1 + (r_bps + h_bps) / 10_000)
    if tick_size > 0:
        bid = math.floor(min(bid, mid - tick_size) / tick_size + 1e-9) * tick_size
        ask = math.ceil(max(ask, mid + tick_size) / tick_size - 1e-9) * tick_size
        bid, ask = round(bid, 10), round(ask, 10)
    return bid, ask
