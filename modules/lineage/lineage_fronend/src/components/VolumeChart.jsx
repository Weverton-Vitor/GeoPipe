import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend
} from "recharts";

import styles from "./VolumeChart.module.css";


/* ---------------- Tooltip custom ---------------- */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

console.log("Tooltip payload:", payload);
  const volume = payload.find(p => p.dataKey === "volume_m2")?.value;
  const ana = payload.find(p => p.dataKey === "ana_volume")?.value;
  const diff = payload[0]?.payload?.days_difference;
  const interp = payload[0]?.payload?.ana_interpolated;

  console.log("CustomTooltip data:", { volume, ana, diff, interp });
  return (
    <div style={{
      background: "black",
      border: "1px solid #ff0000",
      padding: 10,
      borderRadius: 6,
      fontSize: 13,
      boxShadow: "0 2px 6px rgba(0,0,0,0.15)"
    }}>
      <div style={{ marginBottom: 4 }}><strong>{label}</strong></div>

      {volume != null && (
        <div>
          Satélite: <b>{volume.toLocaleString()}</b>
        </div>
      )}

      {ana != null && (
        <div>
          ANA: <b>{ana.toLocaleString()}</b>
          {interp && (
            <span style={{ color: "#ff0000", marginLeft: 6 }}>
              (~{diff} dias)
            </span>
          )}
        </div>
      )}
    </div>
  );
}


/* ---------------- Chart Component ---------------- */
export function VolumeChart({ data, onSelect }) {

  const chartData = (data || []).map(d => ({
    ...d,
    label: `${String(d.day).padStart(2, "0")}/${String(d.month).padStart(2, "0")}/${d.year}`,
  }));


  function handleMouseDown(e) {
    if (!e || e.activeTooltipIndex == null) return;

    const point = chartData[e.activeTooltipIndex];
    if (!point) return;

    onSelect?.(
      point.year,
      String(point.month).padStart(2, "0"),
      String(point.day).padStart(2, "0")
    );
  }


  return (
    <div className={styles.chartContainer}>
      <div className={styles.chartTitle}>
        Volume de água ao longo do tempo
      </div>

      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          onMouseDown={handleMouseDown}
        >

          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="label" />
          <YAxis />

          <Tooltip
            content={<CustomTooltip />}
            cursor={{ stroke: "#aaa", strokeWidth: 1 }}
          />

          <Legend />

          {/* -------- Linha ANA -------- */}
          <Line
            type="monotone"
            dataKey="ana_volume"
            stroke="#7c3aed"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot={false}
            activeDot={false}
            connectNulls
            isAnimationActive={false}
            name="ANA"
            pointerEvents="none"

          />


          {/* -------- Linha principal -------- */}
          <Line
            type="monotone"
            dataKey="volume_m2"
            pointerEvents="none"
            stroke="#000"
            strokeWidth={2}
            dot={(props) => {
              const { cx, cy, payload } = props;

              if (cx == null || cy == null) return null;

              return (
                <circle
                  cx={cx}
                  cy={cy}
                  r={4}
                  fill={payload.ana_interpolated ? "#ef4444" : "#000"}
                />
              );
            }}

            activeDot={{ r: 7 }}
            connectNulls
            isAnimationActive={false}
            name="Satélite"
          />


          {/* -------- Camada invisível clicável -------- */}
<Line
  type="monotone"
  dataKey="volume_m2"
  stroke="transparent"
  strokeWidth={18}
  dot={false}
  activeDot={false}
  connectNulls
  isAnimationActive={false}
  pointerEvents="none"
/>


        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
