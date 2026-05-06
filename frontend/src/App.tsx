import { Activity, AlertTriangle, BarChart3, Play, RefreshCw, ShieldCheck, TrendingUp, Wallet } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { MetricCard } from "./components/MetricCard";
import { PerformanceChart } from "./components/PerformanceChart";
import { TradeLogTable } from "./components/TradeLogTable";
import { DashboardData, fallbackData, fetchSimulation, normalizeSimulationPayload, runSimulation } from "./lib/simulation";

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const percent = new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 2 });
const DRAWDOWN_ALERT_THRESHOLD = -0.1;

export default function App() {
  const [dashboard, setDashboard] = useState<DashboardData>(fallbackData);
  const [isRunning, setIsRunning] = useState(false);
  const [feedStatus, setFeedStatus] = useState("Demo feed loaded");
  const [showRiskAlert, setShowRiskAlert] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const streamUrl = import.meta.env.VITE_SIMULATION_STREAM_URL as string | undefined;
    if (streamUrl && typeof EventSource !== "undefined") {
      const source = new EventSource(streamUrl);
      eventSourceRef.current = source;
      source.onmessage = (event) => {
        setDashboard(normalizeSimulationPayload(JSON.parse(event.data)));
        setFeedStatus("Live stream connected");
      };
      source.onerror = () => setFeedStatus("Live stream paused; showing latest cached run");
      return () => source.close();
    }

    const poll = async () => {
      try {
        const next = await fetchSimulation();
        setDashboard(next);
        setFeedStatus("Polling latest simulation");
      } catch {
        setFeedStatus("Waiting for Member 2 API; demo data active");
      }
    };

    poll();
    const timer = window.setInterval(poll, 5000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    setShowRiskAlert(dashboard.metrics.max_drawdown <= DRAWDOWN_ALERT_THRESHOLD);
  }, [dashboard.metrics.max_drawdown]);

  const kpis = useMemo(
    () => [
      {
        label: "Portfolio Value",
        value: currency.format(dashboard.metrics.portfolio_value),
        detail: `${percent.format(dashboard.metrics.total_return ?? 0)} total return`,
        icon: Wallet,
        tone: "emerald" as const
      },
      {
        label: "Sharpe Ratio",
        value: dashboard.metrics.sharpe_ratio.toFixed(2),
        detail: "Annualized risk-adjusted return",
        icon: TrendingUp,
        tone: "sky" as const
      },
      {
        label: "Max Drawdown",
        value: percent.format(dashboard.metrics.max_drawdown),
        detail: "Worst peak-to-trough decline",
        icon: ShieldCheck,
        tone: dashboard.metrics.max_drawdown <= DRAWDOWN_ALERT_THRESHOLD ? "rose" as const : "amber" as const
      },
      {
        label: "Alpha",
        value: percent.format(dashboard.metrics.alpha),
        detail: `Beta ${Number(dashboard.metrics.beta ?? 0).toFixed(2)} vs benchmark`,
        icon: BarChart3,
        tone: "emerald" as const
      }
    ],
    [dashboard]
  );

  async function handleRunSimulation() {
    setIsRunning(true);
    try {
      const next = await runSimulation();
      setDashboard(next);
      setFeedStatus("Simulation run complete");
    } catch {
      setFeedStatus("Run endpoint unavailable; keeping current dashboard state");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-slate-950 text-white">
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(45,212,191,0.20),transparent_28%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.16),transparent_25%),linear-gradient(135deg,#020617_0%,#0f172a_48%,#111827_100%)]" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-5 rounded-lg border border-white/15 bg-white/10 p-5 shadow-glass backdrop-blur-md md:flex-row md:items-center md:justify-between">
          <div>
            <p className="flex items-center gap-2 text-sm font-medium text-cyan-200">
              <Activity className="h-4 w-4" aria-hidden="true" /> Hedge Fund Risk Modeling System
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-normal text-white md:text-4xl">Risk Analytics Dashboard</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
              Real-time portfolio KPIs, benchmark comparison, and explainable trade rationale for judge-ready analysis.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-lg border border-white/10 bg-slate-950/35 px-3 py-2 text-sm text-slate-300">{feedStatus}</span>
            <button
              type="button"
              onClick={handleRunSimulation}
              disabled={isRunning}
              className="inline-flex h-11 items-center gap-2 rounded-lg bg-cyan-300 px-4 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isRunning ? <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Play className="h-4 w-4" aria-hidden="true" />}
              Run Simulation
            </button>
          </div>
        </header>

        {showRiskAlert && (
          <div className="fixed right-4 top-4 z-20 flex max-w-sm gap-3 rounded-lg border border-rose-300/30 bg-rose-500/20 p-4 text-rose-50 shadow-glass backdrop-blur-md">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <div>
              <p className="font-semibold">Risk Alert</p>
              <p className="text-sm text-rose-100">Maximum drawdown exceeded the 10% guardrail.</p>
            </div>
          </div>
        )}

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {kpis.map((kpi) => (
            <MetricCard key={kpi.label} {...kpi} />
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-12">
          <PerformanceChart data={dashboard.chart} />
          <TradeLogTable trades={dashboard.trades} />
        </section>
      </div>
    </main>
  );
}
