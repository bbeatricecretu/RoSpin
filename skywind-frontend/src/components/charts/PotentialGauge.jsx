// PotentialGauge.tsx
import {
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
} from "recharts";
import { useMemo } from "react";

export default function PotentialGauge({ value }) {
  const v = Math.max(0, Math.min(100, Number(value)));

  // Build chart data
  const data = useMemo(() => [
    { name: "bg", value: 100, fill: "var(--gauge-bg)" },
    { name: "fg", value: v,   fill: "url(#gauge-gradient)" },
  ], [v]);

  return (
    <div
      style={{
        width: "100%",
        maxWidth: "320px",
        margin: "0 auto",
        position: "relative",
      }}
    >
      <RadialBarChart
        width={300}
        height={200}
        cx="50%"
        cy="100%"
        innerRadius="55%"
        outerRadius="95%"
        barSize={26}
        startAngle={180}
        endAngle={0}
        data={data}
      >
        {/* Gradient */}
        <defs>
          <linearGradient id="gauge-gradient" x1="0" y1="1" x2="1" y2="0">
            <stop offset="0%" stopColor="#74c69d" />
            <stop offset="50%" stopColor="#52b788" />
            <stop offset="100%" stopColor="#2d6a4f" />
          </linearGradient>

          {/* Background color */}
          <style>
            {`
              :root {
                --gauge-bg: #e9ecef;
              }
            `}
          </style>
        </defs>

        {/* Background arc */}
        <RadialBar
          data={[data[0]]}
          dataKey="value"
          cornerRadius={30}
        />

        {/* Foreground arc */}
        <RadialBar
          data={[data[1]]}
          dataKey="value"
          cornerRadius={30}
          isAnimationActive={true}
          animationDuration={800}
        />

        <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
      </RadialBarChart>

      {/* Center text */}
      <div
        style={{
          position: "absolute",
          top: "65px",
          width: "100%",
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontSize: "3rem",
            fontWeight: 600,
            color: "#2d6a4f",
            letterSpacing: "-1px",
          }}
        >
          {v.toFixed(1)}
        </span>
        <span
          style={{
            marginLeft: "4px",
            fontSize: "1.2rem",
            color: "#6c757d",
          }}
        >
          /100
        </span>
      </div>
    </div>
  );
}
