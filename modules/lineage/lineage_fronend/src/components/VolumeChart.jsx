import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import styles from "./VolumeChart.module.css";
export function VolumeChart({ data, onSelect }) {
  const chartData = data.map((d) => ({
    ...d,
    label: `${String(d.day).padStart(2, "0")}/${String(d.month).padStart(2, "0")}/${d.year}`,
  }));

  function handleMouseDown(e) {
    if (
      !e ||
      e.activeTooltipIndex === undefined ||
      e.activeTooltipIndex === null
    )
      return;

    const point = chartData[e.activeTooltipIndex];
    if (!point) return;

    const monthFormatted = String(point.month).padStart(2, "0");
    const dayFormatted = String(point.day).padStart(2, "0");

  onSelect(point.year, monthFormatted, dayFormatted);  }

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
          <XAxis dataKey="label" />
          <YAxis />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="volume_m2"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 7 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

