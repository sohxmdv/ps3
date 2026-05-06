import { LucideIcon } from "lucide-react";

type MetricCardProps = {
  label: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone?: "emerald" | "sky" | "amber" | "rose";
};

const tones = {
  emerald: "from-emerald-400/25 to-teal-400/10 text-emerald-100 ring-emerald-300/25",
  sky: "from-sky-400/25 to-cyan-400/10 text-sky-100 ring-sky-300/25",
  amber: "from-amber-300/25 to-orange-400/10 text-amber-100 ring-amber-300/25",
  rose: "from-rose-400/25 to-pink-400/10 text-rose-100 ring-rose-300/25"
};

export function MetricCard({ label, value, detail, icon: Icon, tone = "sky" }: MetricCardProps) {
  return (
    <section className="rounded-lg border border-white/15 bg-white/10 p-5 shadow-glass backdrop-blur-md">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-300">{label}</p>
          <p className="mt-3 text-2xl font-semibold tracking-normal text-white">{value}</p>
        </div>
        <div className={`rounded-lg bg-gradient-to-br p-2 ring-1 ${tones[tone]}`}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
      <p className="mt-4 text-sm text-slate-400">{detail}</p>
    </section>
  );
}
