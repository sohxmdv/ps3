import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartPoint } from "../lib/simulation";

type PerformanceChartProps = {
  data: ChartPoint[];
};

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0
});

export function PerformanceChart({ data }: PerformanceChartProps) {
  return (
    <section className="rounded-lg border border-white/15 bg-white/10 p-5 shadow-glass backdrop-blur-md lg:col-span-8">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">Performance Curve</h2>
          <p className="text-sm text-slate-400">Portfolio value compared with the normalized equity benchmark.</p>
        </div>
        <div className="flex items-center gap-4 text-sm text-slate-300">
          <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-cyan-300" />Portfolio</span>
          <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-amber-300" />Benchmark</span>
        </div>
      </div>

      <div className="h-[360px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 12, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="portfolioFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#67e8f9" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#67e8f9" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="benchmarkFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#fcd34d" stopOpacity={0.26} />
                <stop offset="95%" stopColor="#fcd34d" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
            <XAxis dataKey="date" stroke="#94a3b8" tickLine={false} axisLine={false} minTickGap={36} />
            <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} tickFormatter={(value) => currency.format(Number(value))} width={86} />
            <Tooltip
              contentStyle={{
                background: "rgba(15, 23, 42, 0.88)",
                border: "1px solid rgba(255,255,255,0.14)",
                borderRadius: 8,
                color: "#e2e8f0",
                backdropFilter: "blur(14px)"
              }}
              formatter={(value, name) => [currency.format(Number(value ?? 0)), name === "portfolio" ? "Portfolio" : "Benchmark"]}
              labelStyle={{ color: "#f8fafc" }}
            />
            <Area type="monotone" dataKey="benchmark" stroke="#fcd34d" strokeWidth={2} fill="url(#benchmarkFill)" />
            <Area type="monotone" dataKey="portfolio" stroke="#67e8f9" strokeWidth={3} fill="url(#portfolioFill)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
