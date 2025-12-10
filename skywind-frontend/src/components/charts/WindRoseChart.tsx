import React, { useMemo } from "react";
import { PolarAngleAxis, PolarGrid, Radar, RadarChart, PolarRadiusAxis, Tooltip } from "recharts";

type Rose = {
  N: number; NE: number; E: number; SE: number;
  S: number; SW: number; W: number; NW: number;
};

// Custom tooltip component
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: "white",
        padding: "8px 12px",
        border: "2px solid #2d6a4f",
        borderRadius: "8px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)"
      }}>
        <p style={{ 
          margin: 0, 
          fontWeight: 600,
          color: "#2d6a4f",
          fontSize: "14px"
        }}>
          {payload[0].payload.direction}
        </p>
        <p style={{ 
          margin: "4px 0 0 0",
          color: "#256d57",
          fontSize: "13px"
        }}>
          {payload[0].value.toFixed(2)} m/s
        </p>
      </div>
    );
  }
  return null;
};

export default function WindRoseChart({ data }: { data: Rose }) {
  // Transform wind rose data into format needed for radar chart
  const chartData = useMemo(() => [
    { direction: "N", speed: data.N || 0 },
    { direction: "NE", speed: data.NE || 0 },
    { direction: "E", speed: data.E || 0 },
    { direction: "SE", speed: data.SE || 0 },
    { direction: "S", speed: data.S || 0 },
    { direction: "SW", speed: data.SW || 0 },
    { direction: "W", speed: data.W || 0 },
    { direction: "NW", speed: data.NW || 0 },
  ], [data]);

  const maxSpeed = Math.max(...chartData.map(d => d.speed), 1);

  return (
    <div style={{ 
      width: "100%", 
      display: "flex", 
      flexDirection: "column", 
      alignItems: "center",
      padding: "20px 0"
    }}>
      <div style={{
        width: "100%",
        maxWidth: "400px",
        height: "400px"
      }}>
        <RadarChart
          width={400}
          height={400}
          data={chartData}
          margin={{ top: 20, right: 50, bottom: 20, left: 50 }}
        >
          <defs>
            <linearGradient id="windGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2d6a4f" stopOpacity={0.8} />
              <stop offset="100%" stopColor="#52b788" stopOpacity={0.3} />
            </linearGradient>
          </defs>
          
          <PolarGrid 
            stroke="#cbe8df" 
            strokeWidth={1.5}
          />
          
          <PolarAngleAxis 
            dataKey="direction" 
            tick={{ 
              fill: "#256d57", 
              fontSize: 14,
              fontWeight: 600
            }}
          />
          
          <PolarRadiusAxis 
            angle={90} 
            domain={[0, Math.ceil(maxSpeed)]}
            tick={{ fill: "#6c757d", fontSize: 11 }}
            tickCount={5}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Radar
            name="Wind Speed"
            dataKey="speed"
            stroke="#2d6a4f"
            fill="url(#windGradient)"
            fillOpacity={0.7}
            strokeWidth={2}
          />
        </RadarChart>
      </div>

      <div style={{
        marginTop: "16px",
        textAlign: "center",
        color: "#256d57"
      }}>
        <div style={{ 
          fontSize: "0.9rem", 
          color: "#6c757d",
          marginTop: "8px"
        }}>
          Wind speed in m/s by direction
        </div>
      </div>
    </div>
  );
}

