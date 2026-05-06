import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { TradeLog } from "../lib/simulation";

type TradeLogTableProps = {
  trades: TradeLog[];
};

export function TradeLogTable({ trades }: TradeLogTableProps) {
  const [query, setQuery] = useState("");
  const filteredTrades = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return trades;
    return trades.filter((trade) =>
      [trade.date, trade.action, trade.asset, trade.rationale, trade.riskCheck]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle))
    );
  }, [query, trades]);

  return (
    <section className="rounded-lg border border-white/15 bg-white/10 p-5 shadow-glass backdrop-blur-md lg:col-span-4">
      <div className="mb-5 flex flex-col gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Strategy Log</h2>
          <p className="text-sm text-slate-400">Every trade includes its signal and risk rationale.</p>
        </div>
        <label className="flex h-11 items-center gap-2 rounded-lg border border-white/10 bg-slate-950/35 px-3 text-slate-300 focus-within:border-cyan-300/60">
          <Search className="h-4 w-4" aria-hidden="true" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search logs"
            className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-slate-500"
          />
        </label>
      </div>

      <div className="max-h-[360px] overflow-auto rounded-lg border border-white/10">
        <table className="w-full min-w-[520px] border-collapse text-left text-sm">
          <thead className="sticky top-0 bg-slate-950/85 text-xs uppercase tracking-normal text-slate-400 backdrop-blur-md">
            <tr>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Action</th>
              <th className="px-4 py-3 font-medium">Asset</th>
              <th className="px-4 py-3 font-medium">Rationale</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10 text-slate-200">
            {filteredTrades.map((trade) => (
              <tr key={trade.id} className="bg-white/[0.03] align-top transition hover:bg-white/[0.07]">
                <td className="whitespace-nowrap px-4 py-3 text-slate-300">{trade.date}</td>
                <td className="px-4 py-3">
                  <span className="rounded-md border border-white/10 bg-white/10 px-2 py-1 text-xs font-semibold text-cyan-100">
                    {trade.action}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-300">{trade.asset ?? "Portfolio"}</td>
                <td className="px-4 py-3 leading-6 text-slate-200">{trade.rationale}</td>
              </tr>
            ))}
            {filteredTrades.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-400">No matching strategy logs.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
