import React from "react";

export default function VerdictStamp({ verdict }) {
  let colorClass = "";
  let textColor = "";
  let stampText = "";

  if (verdict === "RECOMMEND") {
    colorClass = "border-stamp-green text-stamp-green bg-stamp-green/5";
    textColor = "#4B5D3A";
    stampText = "RECOMMEND";
  } else if (verdict === "CONSIDER") {
    colorClass = "border-ink text-ink bg-ink/5";
    textColor = "#1F1B16";
    stampText = "CONSIDER";
  } else {
    colorClass = "border-red-flag text-red-flag bg-red-flag/5";
    textColor = "#C1381F";
    stampText = "PASS";
  }

  return (
    <div className="flex items-center justify-center p-4 select-none">
      <div
        className={`relative flex items-center justify-center transform rotate-[-8deg] border-4 border-double px-6 py-2 rounded font-courier font-black text-2xl md:text-3xl uppercase tracking-widest ${colorClass} shadow-[0_0_1px_rgba(0,0,0,0.1)]`}
        style={{
          boxShadow: `inset 0 0 4px ${textColor}22, 0 4px 6px -1px rgba(0,0,0,0.1)`,
          animation: "stampDown 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards",
          opacity: 0,
          transform: "scale(2.5) rotate(-25deg)",
        }}
      >
        {/* Distressed SVG mask or overlays inside the border for that real ink stamp texture */}
        <span className="relative z-10">{stampText}</span>

        {/* CSS Animation Keyframes Inject */}
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes stampDown {
            0% {
              opacity: 0;
              transform: scale(2.5) rotate(-25deg);
            }
            85% {
              opacity: 0.9;
              transform: scale(0.95) rotate(-6deg);
            }
            100% {
              opacity: 0.85;
              transform: scale(1) rotate(-8deg);
            }
          }
        `}} />
      </div>
    </div>
  );
}
