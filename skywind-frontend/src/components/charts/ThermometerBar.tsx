import React from "react";

export default function ThermometerBar({ value }: { value: number }) {
  const temp = Math.max(-20, Math.min(40, value));
  const percent = ((temp + 20) / 60) * 100;

  return (
    <div className="thermo-container">
      <div className="thermo-bar">
        <div
          className="thermo-fill"
          style={{
            height: `${percent}%`,
          }}
        ></div>
      </div>

      <div className="thermo-label">
        <span className="thermo-value">{temp.toFixed(1)}</span>
        <span className="thermo-unit">°C</span>
      </div>
    </div>
  );
}
