"""Financial analytics for the hedge fund risk dashboard.

The functions in this module are intentionally framework-agnostic so Member 2 can
call them from FastAPI and Member 3 can test them independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252
DEFAULT_BENCHMARK_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "equity_dataset.csv"


@dataclass(frozen=True)
class PerformanceMetrics:
    portfolio_value: float
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    alpha: float
    beta: float

    def to_dict(self) -> dict[str, float]:
        return {
            "portfolio_value": round_float(self.portfolio_value),
            "total_return": round_float(self.total_return),
            "annualized_return": round_float(self.annualized_return),
            "annualized_volatility": round_float(self.annualized_volatility),
            "sharpe_ratio": round_float(self.sharpe_ratio),
            "max_drawdown": round_float(self.max_drawdown),
            "alpha": round_float(self.alpha),
            "beta": round_float(self.beta),
        }


def round_float(value: float, digits: int = 6) -> float:
    if value is None or not np.isfinite(value):
        return 0.0
    return round(float(value), digits)


def portfolio_states_to_frame(states: Iterable[dict[str, Any]]) -> pd.DataFrame:
    """Convert Member 2's simulation payload into a typed time-indexed DataFrame."""
    frame = pd.DataFrame(list(states))
    if frame.empty:
        return pd.DataFrame(columns=["value"], index=pd.DatetimeIndex([], name="date"))

    if "date" not in frame.columns or "value" not in frame.columns:
        raise ValueError("Portfolio states must include 'date' and 'value' fields.")

    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna(subset=["date", "value"]).sort_values("date")
    frame = frame.drop_duplicates(subset="date", keep="last")
    return frame.set_index("date")


def calculate_daily_returns(values: pd.Series | Iterable[float]) -> pd.Series:
    series = pd.Series(values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
    if series.size < 2:
        return pd.Series(dtype="float64")
    return series.pct_change().replace([np.inf, -np.inf], np.nan).dropna()


def calculate_sharpe_ratio(
    values: pd.Series | Iterable[float],
    risk_free_rate: float = 0.02,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """Annualized Sharpe ratio using daily portfolio value observations."""
    returns = calculate_daily_returns(values)
    if returns.empty:
        return 0.0

    daily_risk_free = (1.0 + risk_free_rate) ** (1.0 / periods_per_year) - 1.0
    excess_returns = returns - daily_risk_free
    volatility = excess_returns.std(ddof=1)
    if not np.isfinite(volatility) or volatility == 0:
        return 0.0

    return float(np.sqrt(periods_per_year) * excess_returns.mean() / volatility)


def calculate_max_drawdown(values: pd.Series | Iterable[float]) -> float:
    """Return the worst peak-to-trough drawdown as a negative percentage."""
    series = pd.Series(values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
    if series.empty:
        return 0.0

    running_peak = series.cummax()
    drawdowns = (series / running_peak) - 1.0
    return float(drawdowns.min())


def load_equity_benchmark(
    benchmark_path: str | Path = DEFAULT_BENCHMARK_PATH,
    date_column: str = "Date",
) -> pd.DataFrame:
    """Load equity benchmark prices and return a date-indexed frame with returns."""
    path = Path(benchmark_path)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark file not found: {path}")

    frame = pd.read_csv(path)
    if date_column not in frame.columns:
        raise ValueError(f"Benchmark file must include a '{date_column}' column.")

    frame = frame.copy()
    frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
    price_column = infer_price_column(frame, excluded={date_column})
    frame[price_column] = pd.to_numeric(frame[price_column], errors="coerce")
    frame = frame.dropna(subset=[date_column, price_column]).sort_values(date_column)
    frame = frame.drop_duplicates(subset=date_column, keep="last")
    frame = frame.set_index(date_column)
    frame["benchmark_return"] = frame[price_column].pct_change()
    return frame[[price_column, "benchmark_return"]].rename(columns={price_column: "benchmark_value"})


def infer_price_column(frame: pd.DataFrame, excluded: set[str]) -> str:
    preferred = ["Adj Close", "Adj_Close", "Close", "close", "Price", "price", "Value", "value"]
    for column in preferred:
        if column in frame.columns and column not in excluded:
            return column

    numeric_candidates = [
        column
        for column in frame.columns
        if column not in excluded and pd.to_numeric(frame[column], errors="coerce").notna().any()
    ]
    if not numeric_candidates:
        raise ValueError("Could not infer benchmark price column.")
    return numeric_candidates[0]


def calculate_alpha_beta(
    portfolio_values: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> tuple[float, float]:
    """Compute annualized CAPM alpha and beta against benchmark daily returns."""
    portfolio_returns = calculate_daily_returns(portfolio_values)
    aligned = pd.concat(
        [portfolio_returns.rename("portfolio"), benchmark_returns.rename("benchmark")],
        axis=1,
        join="inner",
    ).dropna()

    if aligned.shape[0] < 2:
        return 0.0, 0.0

    benchmark_variance = aligned["benchmark"].var(ddof=1)
    if not np.isfinite(benchmark_variance) or benchmark_variance == 0:
        beta = 0.0
    else:
        beta = float(aligned["portfolio"].cov(aligned["benchmark"]) / benchmark_variance)

    daily_risk_free = (1.0 + risk_free_rate) ** (1.0 / periods_per_year) - 1.0
    daily_alpha = (aligned["portfolio"].mean() - daily_risk_free) - beta * (
        aligned["benchmark"].mean() - daily_risk_free
    )
    annualized_alpha = (1.0 + daily_alpha) ** periods_per_year - 1.0
    return float(annualized_alpha), beta


def calculate_performance_metrics(
    portfolio_states: Iterable[dict[str, Any]] | pd.DataFrame,
    benchmark_path: str | Path = DEFAULT_BENCHMARK_PATH,
    risk_free_rate: float = 0.02,
) -> dict[str, float]:
    """Calculate all dashboard KPIs from simulation output and equity benchmark CSV."""
    if isinstance(portfolio_states, pd.DataFrame):
        portfolio_frame = portfolio_states.copy()
        if "date" in portfolio_frame.columns:
            portfolio_frame["date"] = pd.to_datetime(portfolio_frame["date"], errors="coerce")
            portfolio_frame = portfolio_frame.dropna(subset=["date"]).set_index("date")
    else:
        portfolio_frame = portfolio_states_to_frame(portfolio_states)

    if portfolio_frame.empty or "value" not in portfolio_frame.columns:
        return PerformanceMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0).to_dict()

    values = pd.to_numeric(portfolio_frame["value"], errors="coerce").dropna()
    returns = calculate_daily_returns(values)
    benchmark = load_equity_benchmark(benchmark_path)
    alpha, beta = calculate_alpha_beta(values, benchmark["benchmark_return"], risk_free_rate)

    total_return = float(values.iloc[-1] / values.iloc[0] - 1.0) if values.size > 1 and values.iloc[0] else 0.0
    annualized_return = 0.0
    if values.size > 1 and values.iloc[0] > 0:
        years = max((values.index[-1] - values.index[0]).days / 365.25, 1 / TRADING_DAYS_PER_YEAR)
        annualized_return = float((values.iloc[-1] / values.iloc[0]) ** (1.0 / years) - 1.0)

    annualized_volatility = float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)) if returns.size > 1 else 0.0

    return PerformanceMetrics(
        portfolio_value=float(values.iloc[-1]),
        total_return=total_return,
        annualized_return=annualized_return,
        annualized_volatility=annualized_volatility,
        sharpe_ratio=calculate_sharpe_ratio(values, risk_free_rate),
        max_drawdown=calculate_max_drawdown(values),
        alpha=alpha,
        beta=beta,
    ).to_dict()


def build_equity_curve_payload(
    portfolio_states: Iterable[dict[str, Any]],
    benchmark_path: str | Path = DEFAULT_BENCHMARK_PATH,
) -> list[dict[str, Any]]:
    """Return chart-ready portfolio and normalized benchmark values."""
    portfolio = portfolio_states_to_frame(portfolio_states)
    if portfolio.empty:
        return []

    benchmark = load_equity_benchmark(benchmark_path)
    merged = portfolio[["value"]].join(benchmark[["benchmark_value"]], how="left")
    merged["benchmark_value"] = merged["benchmark_value"].ffill().bfill()
    start_portfolio = merged["value"].iloc[0]
    start_benchmark = merged["benchmark_value"].iloc[0]

    if not start_portfolio or not start_benchmark:
        return []

    merged["portfolio"] = merged["value"]
    merged["benchmark"] = merged["benchmark_value"] / start_benchmark * start_portfolio
    return [
        {
            "date": index.strftime("%Y-%m-%d"),
            "portfolio": round_float(row["portfolio"], 2),
            "benchmark": round_float(row["benchmark"], 2),
        }
        for index, row in merged.iterrows()
    ]
