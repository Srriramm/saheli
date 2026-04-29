import { useEffect, useRef } from "react";

export default function SaheliLogo() {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "100vh",
      background: "#FAFAFA",
      fontFamily: "sans-serif"
    }}>
      {/* ── LOGO CARD ── */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "32px",
        padding: "40px 56px",
        background: "white",
        borderRadius: "4px",
        boxShadow: "0 2px 24px rgba(0,0,0,0.07)"
      }}>

        {/* ── ICON MARK ── */}
        <svg width="90" height="120" viewBox="0 0 90 120" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="ig" x1="0" y1="0" x2="90" y2="120" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#B5330A"/>
              <stop offset="100%" stopColor="#E0622A"/>
            </linearGradient>
          </defs>

          {/* Head */}
          <circle cx="45" cy="22" r="18" stroke="url(#ig)" strokeWidth="5" fill="none"/>

          {/* Bindi — small filled dot above center */}
          <circle cx="45" cy="13" r="4.5" fill="#C1390E"/>

          {/* Neck */}
          <line x1="45" y1="40" x2="45" y2="52" stroke="url(#ig)" strokeWidth="5" strokeLinecap="round"/>

          {/* Shoulders */}
          <path d="M 12 72 Q 12 52 45 52 Q 78 52 78 72" stroke="url(#ig)" strokeWidth="5" fill="none" strokeLinecap="round"/>

          {/* Pregnant belly arc */}
          <path d="M 20 72 Q 14 100 45 108 Q 76 100 70 72" stroke="url(#ig)" strokeWidth="5" fill="none" strokeLinecap="round"/>

          {/* Heart inside belly */}
          <path d="M45 97 C45 97 35 90 35 84 C35 80 38.5 78 41.5 80 C43 81 44 83 45 84.5 C46 83 47 81 48.5 80 C51.5 78 55 80 55 84 C55 90 45 97 45 97Z"
                fill="#C1390E" opacity="0.8"/>
        </svg>

        {/* ── DIVIDER ── */}
        <div style={{
          width: "1.5px",
          height: "90px",
          background: "linear-gradient(to bottom, transparent, #C1390E55, transparent)"
        }}/>

        {/* ── TEXT MARK ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <div style={{
            fontFamily: "Georgia, 'Palatino Linotype', serif",
            fontSize: "62px",
            fontWeight: "700",
            letterSpacing: "8px",
            color: "#1A1A1A",
            lineHeight: 1,
          }}>SAHELI</div>

          {/* Rule */}
          <div style={{
            height: "2px",
            background: "linear-gradient(to right, #C1390E, #E0622A, transparent)",
            borderRadius: "2px",
            width: "100%"
          }}/>

          <div style={{
            fontFamily: "'Trebuchet MS', 'Gill Sans', sans-serif",
            fontSize: "12px",
            letterSpacing: "3.5px",
            color: "#AAA",
            fontWeight: "400"
          }}>MATERNAL HEALTH · EVERY VILLAGE</div>
        </div>

      </div>

      {/* ── ICON ONLY version below ── */}
      <div style={{
        position: "absolute",
        bottom: "40px",
        display: "flex",
        gap: "24px",
        alignItems: "center"
      }}>
        <span style={{ fontSize: "12px", color: "#BBB", letterSpacing: "2px" }}>ICON ONLY VERSION</span>
        <div style={{
          width: "64px", height: "64px",
          borderRadius: "50%",
          background: "#FDF0EB",
          display: "flex",
          alignItems: "center",
          justifyContent: "center"
        }}>
          <svg width="38" height="52" viewBox="0 0 90 120" fill="none">
            <defs>
              <linearGradient id="ig2" x1="0" y1="0" x2="90" y2="120" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#B5330A"/>
                <stop offset="100%" stopColor="#E0622A"/>
              </linearGradient>
            </defs>
            <circle cx="45" cy="22" r="18" stroke="url(#ig2)" strokeWidth="5" fill="none"/>
            <circle cx="45" cy="13" r="4.5" fill="#C1390E"/>
            <line x1="45" y1="40" x2="45" y2="52" stroke="url(#ig2)" strokeWidth="5" strokeLinecap="round"/>
            <path d="M 12 72 Q 12 52 45 52 Q 78 52 78 72" stroke="url(#ig2)" strokeWidth="5" fill="none" strokeLinecap="round"/>
            <path d="M 20 72 Q 14 100 45 108 Q 76 100 70 72" stroke="url(#ig2)" strokeWidth="5" fill="none" strokeLinecap="round"/>
            <path d="M45 97 C45 97 35 90 35 84 C35 80 38.5 78 41.5 80 C43 81 44 83 45 84.5 C46 83 47 81 48.5 80 C51.5 78 55 80 55 84 C55 90 45 97 45 97Z" fill="#C1390E" opacity="0.8"/>
          </svg>
        </div>

        <div style={{
          width: "48px", height: "48px",
          borderRadius: "12px",
          background: "#C1390E",
          display: "flex",
          alignItems: "center",
          justifyContent: "center"
        }}>
          <svg width="28" height="38" viewBox="0 0 90 120" fill="none">
            <circle cx="45" cy="22" r="18" stroke="white" strokeWidth="6" fill="none"/>
            <circle cx="45" cy="13" r="4.5" fill="white"/>
            <line x1="45" y1="40" x2="45" y2="52" stroke="white" strokeWidth="6" strokeLinecap="round"/>
            <path d="M 12 72 Q 12 52 45 52 Q 78 52 78 72" stroke="white" strokeWidth="6" fill="none" strokeLinecap="round"/>
            <path d="M 20 72 Q 14 100 45 108 Q 76 100 70 72" stroke="white" strokeWidth="6" fill="none" strokeLinecap="round"/>
            <path d="M45 97 C45 97 35 90 35 84 C35 80 38.5 78 41.5 80 C43 81 44 83 45 84.5 C46 83 47 81 48.5 80 C51.5 78 55 80 55 84 C55 90 45 97 45 97Z" fill="white" opacity="0.9"/>
          </svg>
        </div>
      </div>

    </div>
  );
}
