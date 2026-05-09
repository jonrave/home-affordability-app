import { AffordabilityOutputs } from "../lib/api";
import { compactMoney } from "../lib/formatters";

type ProjectionChartProps = {
  description?: string;
  rows: AffordabilityOutputs["projection"];
};

const series = [
  { key: "liquid_investments", label: "Liquid nominal", color: "#0f8f72" },
  { key: "liquid_real", label: "Liquid real", color: "#237f91" },
  { key: "retirement_nonliquid_investments", label: "Retirement/non-liquid", color: "#6f55a8" },
  { key: "liquidity_reserve_target", label: "Reserve target", color: "#ba6b14" }
] as const;

export function ProjectionChart({
  description = "Shows whether modeled liquid assets stay above the reserve target after inflation.",
  rows
}: ProjectionChartProps) {
  const width = 860;
  const height = 320;
  const padding = { top: 18, right: 18, bottom: 34, left: 70 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const maxValue = Math.max(
    ...rows.flatMap((row) => series.map((item) => Number(row[item.key]))),
    1
  );
  const roundedMax = Math.ceil(maxValue / 500_000) * 500_000;

  function x(year: number) {
    const maxYear = Math.max(rows.length - 1, 1);
    return padding.left + (year / maxYear) * chartWidth;
  }

  function y(value: number) {
    return padding.top + chartHeight - (value / roundedMax) * chartHeight;
  }

  function points(key: (typeof series)[number]["key"]) {
    return rows.map((row) => `${x(row.year)},${y(Number(row[key]))}`).join(" ");
  }

  const yTicks = [0, roundedMax / 2, roundedMax];
  const xTicks = [0, 10, 20, 30].filter((tick) => tick <= rows.length - 1);

  return (
    <section className="panel projection-panel">
      <div className="section-heading">
        <div>
          <h2>30-Year Projection</h2>
          <p>{description}</p>
        </div>
      </div>

      <div className="chart-wrap" aria-label="30-year projection chart">
        <svg viewBox={`0 0 ${width} ${height}`} role="img">
          <title>30-year projection of liquid assets, real liquid assets, retirement assets, and reserve target</title>
          {yTicks.map((tick) => (
            <g key={tick}>
              <line className="grid-line" x1={padding.left} x2={width - padding.right} y1={y(tick)} y2={y(tick)} />
              <text className="axis-label" x={padding.left - 10} y={y(tick) + 4} textAnchor="end">
                {compactMoney(tick)}
              </text>
            </g>
          ))}
          {xTicks.map((tick) => (
            <text className="axis-label" key={tick} x={x(tick)} y={height - 8} textAnchor="middle">
              Y{tick}
            </text>
          ))}
          {series.map((item) => (
            <polyline
              fill="none"
              key={item.key}
              points={points(item.key)}
              stroke={item.color}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="3"
            />
          ))}
        </svg>
      </div>

      <div className="chart-legend">
        {series.map((item) => (
          <span key={item.key}>
            <i style={{ background: item.color }} />
            {item.label}
          </span>
        ))}
      </div>
    </section>
  );
}
