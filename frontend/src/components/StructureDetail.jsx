import React from "react";

export default function StructureDetail({ detail }) {
  if (!detail) return <p className="font-courier text-sm">No structure details available.</p>;

  const { beats = [], mean_deviation, structural_assessment } = detail;

  return (
    <div className="space-y-6 text-left">
      <div className="border-b border-ink/20 pb-4">
        <h3 className="font-grotesk font-bold text-lg text-ink uppercase tracking-wider">
          Save the Cat Structure Analysis
        </h3>
        <p className="font-grotesk text-sm opacity-80 mt-1">
          Measures structural beat locations against standard industry models.
        </p>
      </div>

      {/* Assessment Commentary */}
      <div className="bg-ink/5 border border-ink/20 p-4 rounded">
        <div className="font-grotesk font-semibold text-xs opacity-60 uppercase mb-1">
          Structural Assessment
        </div>
        <p className="font-grotesk text-sm leading-relaxed">{structural_assessment}</p>
      </div>

      {/* Stats Summary */}
      {mean_deviation !== null && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-ink/20 p-4 rounded bg-paper">
            <div className="font-grotesk font-semibold text-xs opacity-60 uppercase mb-1 text-ink/75">
              Mean Beat Deviation
            </div>
            <div className="font-courier font-bold text-3xl text-carbon-blue">
              {mean_deviation}%
            </div>
            <p className="text-xs font-grotesk opacity-60 mt-1">
              Average offset from expected page-percentage positions.
            </p>
          </div>
        </div>
      )}

      {/* Beats Table */}
      <div className="border border-ink rounded overflow-hidden">
        <table className="w-full text-left font-grotesk border-collapse">
          <thead>
            <tr className="bg-ink text-paper text-xs uppercase font-bold border-b border-ink">
              <th className="p-3">Beat</th>
              <th className="p-3 text-center">Expected %</th>
              <th className="p-3 text-center">Detected Page</th>
              <th className="p-3 text-center">Detected %</th>
              <th className="p-3 text-center">Deviation</th>
              <th className="p-3 text-center">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink/20 text-sm">
            {beats.map((beat) => {
              const hasDeviation = beat.deviation_pct !== null;
              const isHighDev = hasDeviation && beat.deviation_pct > 15;

              return (
                <tr key={beat.beat_name} className="hover:bg-ink/5 transition-colors">
                  <td className="p-3 font-bold text-ink">{beat.beat_name}</td>
                  <td className="p-3 text-center opacity-85 font-courier">{beat.expected_pct}%</td>
                  <td className="p-3 text-center font-courier">
                    {beat.detected_page !== null ? beat.detected_page : "—"}
                  </td>
                  <td className="p-3 text-center font-courier">
                    {beat.detected_pct !== null ? `${beat.detected_pct}%` : "—"}
                  </td>
                  <td className="p-3 text-center font-courier font-bold">
                    {hasDeviation ? (
                      <span className={isHighDev ? "text-red-flag" : "text-carbon-blue"}>
                        {beat.deviation_pct > 0 ? `+${beat.deviation_pct}%` : `${beat.deviation_pct}%`}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="p-3 text-center">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-bold font-courier uppercase ${
                        beat.confidence === "high"
                          ? "bg-stamp-green/10 text-stamp-green border border-stamp-green/20"
                          : beat.confidence === "medium"
                          ? "bg-ink/10 text-ink border border-ink/20"
                          : "bg-red-flag/10 text-red-flag border border-red-flag/20"
                      }`}
                    >
                      {beat.confidence}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Beat details list (supporting evidence / quotes) */}
      <div className="space-y-4">
        <h4 className="font-grotesk font-bold text-md text-ink uppercase tracking-wide">
          Supporting Beat Evidence
        </h4>
        <div className="space-y-3">
          {beats.map((beat) => (
            <div key={beat.beat_name} className="border border-ink/15 rounded p-4 bg-paper/50">
              <div className="flex items-center justify-between border-b border-ink/10 pb-2 mb-2">
                <span className="font-bold text-sm text-ink">{beat.beat_name}</span>
                <span className="font-courier text-xs text-ink/75 bg-ink/5 px-2 py-0.5 rounded">
                  Page {beat.detected_page || "Unspecified"}
                </span>
              </div>
              <div className="font-courier text-sm leading-relaxed whitespace-pre-line italic opacity-90 pl-3 border-l-2 border-carbon-blue">
                {beat.quote ? `"${beat.quote}"` : "No direct quote available or beat not detected."}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
