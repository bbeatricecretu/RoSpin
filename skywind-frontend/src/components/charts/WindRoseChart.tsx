// CompassBarChart.tsx
import React from "react";

type Rose = {
  N: number; NE: number; E: number; SE: number;
  S: number; SW: number; W: number; NW: number;
};

function getColor(value: number) {
  if (value <= 1) return "#d8f3dc";
  if (value <= 3) return "#95d5b2";
  if (value <= 5) return "#52b788";
  if (value <= 7) return "#2d6a4f";
  return "#1b4332";
}

export default function CompassBarChart({ data }: { data: Rose }) {
  const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const max = Math.max(...dirs.map((d) => data[d] || 0), 1);

  const size = 260;
  const center = size / 2;

  const radius = 90;     // distance to start drawing bars
  const barMax = 60;     // maximum bar length

  const angle = {
    N: -90, NE: -45, E: 0, SE: 45,
    S: 90, SW: 135, W: 180, NW: -135,
  };

  return (
    <svg width={size} height={size} style={{ display: "block", margin: "0 auto" }}>
      {/* Background compass lines */}
      <circle cx={center} cy={center} r={radius + barMax} fill="#f8f9fa" stroke="#e9ecef" />

      {dirs.map((d) => {
        const v = data[d] || 0;
        const len = (v / max) * barMax;
        const theta = (angle[d] * Math.PI) / 180;

        const x1 = center + Math.cos(theta) * radius;
        const y1 = center + Math.sin(theta) * radius;

        const x2 = center + Math.cos(theta) * (radius + len);
        const y2 = center + Math.sin(theta) * (radius + len);

        return (
          <g key={d}>
            <line
              x1={x1} y1={y1}
              x2={x2} y2={y2}
              stroke={getColor(v)}
              strokeWidth={10}
              strokeLinecap="round"
            />

            {/* Label */}
            <text
              x={center + Math.cos(theta) * (radius + barMax + 18)}
              y={center + Math.sin(theta) * (radius + barMax + 18)}
              textAnchor="middle"
              alignmentBaseline="middle"
              fontSize="12"
              fill="#333"
            >
              {d}
            </text>

            {/* Value */}
            <text
              x={x2}
              y={y2 - 8}
              textAnchor="middle"
              fontSize="11"
              fill="#555"
            >
              {v.toFixed(1)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
