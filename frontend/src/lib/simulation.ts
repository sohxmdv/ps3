export type TradeAction = "BUY" | "SELL" | "HOLD" | "REJECTED" | string;

export type TradeLog = {
  id: string;
  date: string;
  action: TradeAction;
  asset?: string;
  quantity?: number;
  price?: number;
  rationale: string;
  riskCheck?: string;
};

export type PortfolioState = {
  date: string;
  value: number;
  cash?: number;
  positions?: Record<string, number>;
  trade_log?: Partial<TradeLog> | Partial<TradeLog>[] | null;
  benchmark?: number;
  equity_benchmark?: number;
};

export type Metrics = {
  portfolio_value: number;
  sharpe_ratio: number;
  max_drawdown: number;
  alpha: number;
  beta?: number;
  annualized_volatility?: number;
  total_return?: number;
};

export type ChartPoint = {
  date: string;
  portfolio: number;
  benchmark: number;
};

export type DashboardData = {
  states: PortfolioState[];
  metrics: Metrics;
  chart: ChartPoint[];
  trades: TradeLog[];
  updatedAt: string;
};

const fallbackStates: PortfolioState[] = [
  { date: "2026-01-02", value: 100000, benchmark: 100000, trade_log: { action: "HOLD", rationale: "Initial capital protected while indicators warmed up." } },
  { date: "2026-01-05", value: 101900, benchmark: 100700, trade_log: { action: "BUY", asset: "EQUITY", quantity: 20, price: 112.4, rationale: "Close price crossed above SMA_10 while VaR stayed below the configured risk limit." } },
  { date: "2026-01-06", value: 103250, benchmark: 101300, trade_log: { action: "HOLD", rationale: "Momentum stayed positive, but position cap prevented adding exposure." } },
  { date: "2026-01-07", value: 100850, benchmark: 100950, trade_log: { action: "SELL", asset: "OIL", quantity: 10, price: 78.1, rationale: "Drawdown guardrail tightened after volatility expanded beyond the risk manager threshold." } },
  { date: "2026-01-08", value: 104650, benchmark: 102000, trade_log: { action: "BUY", asset: "EQUITY", quantity: 15, price: 114.9, rationale: "Trend recovered and available cash supported a smaller risk-adjusted entry." } }
];

export const fallbackData = normalizeSimulationPayload({ states: fallbackStates });

export function normalizeSimulationPayload(payload: unknown): DashboardData {
  const source = payload as Record<string, unknown> | PortfolioState[];
  const states = extractStates(source);
  const metrics = normalizeMetrics((source as Record<string, unknown>)?.metrics, states);
  const chart = normalizeChart((source as Record<string, unknown>)?.equity_curve, states);
  const trades = extractTrades(source, states);

  return {
    states,
    metrics,
    chart,
    trades,
    updatedAt: new Date().toISOString()
  };
}

function extractStates(source: Record<string, unknown> | PortfolioState[]): PortfolioState[] {
  const candidates = Array.isArray(source)
    ? source
    : source.states ?? source.daily_portfolio_values ?? source.portfolio_values ?? source.results ?? [];

  return Array.isArray(candidates)
    ? candidates
        .map((item) => item as PortfolioState)
        .filter((item) => item.date && Number.isFinite(Number(item.value)))
        .map((item) => ({ ...item, value: Number(item.value) }))
    : [];
}

function normalizeMetrics(raw: unknown, states: PortfolioState[]): Metrics {
  const metrics = (raw ?? {}) as Partial<Metrics>;
  const values = states.map((state) => state.value);
  const latest = values.at(-1) ?? 0;
  const drawdown = calculateMaxDrawdown(values);

  return {
    portfolio_value: Number(metrics.portfolio_value ?? latest),
    sharpe_ratio: Number(metrics.sharpe_ratio ?? 0),
    max_drawdown: Number(metrics.max_drawdown ?? drawdown),
    alpha: Number(metrics.alpha ?? 0),
    beta: Number(metrics.beta ?? 0),
    annualized_volatility: Number(metrics.annualized_volatility ?? 0),
    total_return: Number(metrics.total_return ?? (values.length > 1 ? latest / values[0] - 1 : 0))
  };
}

function normalizeChart(raw: unknown, states: PortfolioState[]): ChartPoint[] {
  if (Array.isArray(raw) && raw.length > 0) {
    return raw.map((point) => {
      const row = point as Partial<ChartPoint> & { value?: number };
      return {
        date: String(row.date),
        portfolio: Number(row.portfolio ?? row.value ?? 0),
        benchmark: Number(row.benchmark ?? 0)
      };
    });
  }

  const firstPortfolio = states[0]?.value || 1;
  const firstBenchmark = Number(states.find((state) => state.benchmark || state.equity_benchmark)?.benchmark ?? states.find((state) => state.equity_benchmark)?.equity_benchmark ?? firstPortfolio);

  return states.map((state) => {
    const benchmarkRaw = Number(state.benchmark ?? state.equity_benchmark ?? state.value);
    return {
      date: state.date,
      portfolio: state.value,
      benchmark: firstBenchmark ? (benchmarkRaw / firstBenchmark) * firstPortfolio : state.value
    };
  });
}

function extractTrades(source: Record<string, unknown> | PortfolioState[], states: PortfolioState[]): TradeLog[] {
  const explicit = !Array.isArray(source) ? source.trade_log ?? source.trades ?? source.logs : undefined;
  const rawLogs = Array.isArray(explicit) ? explicit : states.flatMap((state) => normalizeStateLogs(state));

  return rawLogs
    .map((item, index) => {
      const log = item as Partial<TradeLog>;
      return {
        id: String(log.id ?? `${log.date ?? "trade"}-${index}`),
        date: String(log.date ?? states[index]?.date ?? ""),
        action: String(log.action ?? "HOLD"),
        asset: log.asset,
        quantity: log.quantity,
        price: log.price,
        rationale: String(log.rationale ?? "No rationale supplied by the simulation engine."),
        riskCheck: log.riskCheck
      };
    })
    .filter((log) => log.date || log.rationale);
}

function normalizeStateLogs(state: PortfolioState): Partial<TradeLog>[] {
  if (!state.trade_log) return [];
  const logs = Array.isArray(state.trade_log) ? state.trade_log : [state.trade_log];
  return logs.map((log) => ({ ...log, date: log.date ?? state.date }));
}

function calculateMaxDrawdown(values: number[]): number {
  let peak = values[0] ?? 0;
  let maxDrawdown = 0;
  for (const value of values) {
    peak = Math.max(peak, value);
    if (peak > 0) maxDrawdown = Math.min(maxDrawdown, value / peak - 1);
  }
  return maxDrawdown;
}

export async function fetchSimulation(): Promise<DashboardData> {
  // FIXED: Point directly to port 8000
  const response = await fetch("http://localhost:8000/api/simulate/latest", { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`Simulation feed failed: ${response.status}`);
  return normalizeSimulationPayload(await response.json());
}

export async function runSimulation(): Promise<DashboardData> {
  // FIXED: Point directly to port 8000
  const response = await fetch("http://localhost:8000/api/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ risk_free_rate: 0.02, max_drawdown_limit: 0.1 })
  });
  if (!response.ok) throw new Error(`Simulation run failed: ${response.status}`);
  return normalizeSimulationPayload(await response.json());
}