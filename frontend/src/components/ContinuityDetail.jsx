import React from "react";
import { AlertCircle, Calendar, ShieldAlert } from "lucide-react";

export default function ContinuityDetail({ detail }) {
  if (!detail) return <p className="font-courier text-sm">No continuity details available.</p>;

  const { errors = [], continuity_assessment } = detail;

  return (
    <div className="space-y-6 text-left font-grotesk">
      <div className="border-b border-ink/20 pb-4">
        <h3 className="font-bold text-lg text-ink uppercase tracking-wider">
          Continuity & Consistency Analysis
        </h3>
        <p className="text-sm opacity-80 mt-1">
          Flags internal script contradictions in props, timeline, locations, or stated facts.
        </p>
      </div>

      {/* Assessment Commentary */}
      <div className="bg-ink/5 border border-ink/20 p-4 rounded">
        <div className="font-bold text-xs opacity-60 uppercase mb-1">
          Continuity Supervisor Summary
        </div>
        <p className="text-sm leading-relaxed">{continuity_assessment}</p>
      </div>

      {/* Continuity Issues List */}
      <div className="space-y-4">
        <h4 className="font-bold text-md text-ink uppercase tracking-wide flex items-center gap-2">
          Internal Script Contradictions
          {errors.length > 0 && (
            <span className="bg-red-flag text-paper text-xs font-bold font-courier px-2 py-0.5 rounded">
              {errors.length} Flags
            </span>
          )}
        </h4>

        {errors.length === 0 ? (
          <div className="border border-stamp-green/20 bg-stamp-green/5 p-4 rounded text-sm text-center">
            No internal contradictions or continuity errors detected. The screenplay exhibits high integrity.
          </div>
        ) : (
          <div className="space-y-3">
            {errors.map((err, index) => {
              const isMajor = err.severity === "major";

              return (
                <div
                  key={index}
                  className={`border p-4 rounded bg-paper/50 ${
                    isMajor ? "border-red-flag/40 bg-red-flag/5" : "border-ink/15"
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex items-center gap-2 border-b border-ink/10 pb-2 mb-2">
                    <ShieldAlert size={16} className={isMajor ? "text-red-flag" : "text-ink/80"} />
                    <span className="font-bold text-sm text-ink uppercase">
                      Category: {err.error_type} Contradiction
                    </span>
                    <span
                      className={`text-xs font-bold font-courier uppercase px-2 py-0.5 rounded ml-auto ${
                        isMajor ? "bg-red-flag text-paper" : "bg-ink/10 text-ink"
                      }`}
                    >
                      {err.severity}
                    </span>
                  </div>

                  {/* Fact Contradiction Comparison Grid */}
                  <div className="space-y-2">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                      <div className="p-2 border border-ink/10 bg-paper rounded">
                        <div className="font-bold opacity-60 uppercase mb-0.5 flex items-center justify-between">
                          <span>Established Fact</span>
                          <span className="underline font-courier">Page {err.page_introduced || "—"}</span>
                        </div>
                        <p className="font-courier opacity-95 leading-relaxed">{err.established_fact}</p>
                      </div>

                      <div className="p-2 border border-ink/10 bg-paper rounded">
                        <div className="font-bold opacity-60 uppercase mb-0.5 flex items-center justify-between">
                          <span>Violated Contradiction</span>
                          <span className="underline font-courier text-red-flag">Page {err.page_violated || "—"}</span>
                        </div>
                        <p className="font-courier text-red-flag font-semibold leading-relaxed">{err.contradiction}</p>
                      </div>
                    </div>

                    {/* Detailed Analysis Description */}
                    <div className="mt-2 pt-2 text-sm border-t border-ink/5">
                      <span className="font-bold text-xs opacity-60 uppercase">Supervisor Notes: </span>
                      <span className="opacity-95">{err.description}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
