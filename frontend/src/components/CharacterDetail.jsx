import React from "react";
import { User, AlertTriangle } from "lucide-react";

export default function CharacterDetail({ detail }) {
  if (!detail) return <p className="font-courier text-sm">No character details available.</p>;

  const { characters = [], inconsistencies = [], character_assessment } = detail;

  return (
    <div className="space-y-6 text-left">
      <div className="border-b border-ink/20 pb-4">
        <h3 className="font-grotesk font-bold text-lg text-ink uppercase tracking-wider">
          Character Arc & Motivation Analysis
        </h3>
        <p className="font-grotesk text-sm opacity-80 mt-1">
          Tracks protagonist and key supporting character actions against established traits.
        </p>
      </div>

      {/* Assessment Commentary */}
      <div className="bg-ink/5 border border-ink/20 p-4 rounded">
        <div className="font-grotesk font-semibold text-xs opacity-60 uppercase mb-1">
          Swarm Character Assessment
        </div>
        <p className="font-grotesk text-sm leading-relaxed">{character_assessment}</p>
      </div>

      {/* Character Profiles */}
      <div className="space-y-4">
        <h4 className="font-grotesk font-bold text-md text-ink uppercase tracking-wide">
          Tracked Character Profiles
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {characters.map((char) => (
            <div key={char.name} className="border border-ink/20 p-4 rounded bg-paper/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 border-b border-ink/10 pb-2 mb-2">
                  <User size={16} className="text-ink/80" />
                  <span className="font-bold text-sm text-ink uppercase tracking-wide">{char.name}</span>
                  <span className="text-xs font-courier opacity-70 bg-ink/5 px-2 py-0.5 rounded ml-auto">
                    {char.role}
                  </span>
                </div>
                <div className="space-y-2 text-sm font-grotesk">
                  <div>
                    <span className="font-bold text-xs opacity-60 uppercase">Stated Motivation: </span>
                    <span className="opacity-90">{char.stated_motivation || "None explicitly stated."}</span>
                  </div>
                  <div>
                    <span className="font-bold text-xs opacity-60 uppercase">Arc Summary: </span>
                    <p className="opacity-90 mt-0.5 leading-relaxed">{char.arc_summary || "No clear arc tracked."}</p>
                  </div>
                </div>
              </div>

              {/* Character traits */}
              {char.traits && char.traits.length > 0 && (
                <div className="mt-4 pt-3 border-t border-ink/10">
                  <div className="flex flex-wrap gap-1">
                    {char.traits.map((t, idx) => (
                      <span key={idx} className="bg-ink/5 text-ink text-xs font-courier px-2 py-0.5 border border-ink/10 rounded">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Inconsistency Flags */}
      <div className="space-y-4 pt-4">
        <h4 className="font-grotesk font-bold text-md text-ink uppercase tracking-wide flex items-center gap-2">
          Character Trait Inconsistencies
          {inconsistencies.length > 0 && (
            <span className="bg-red-flag text-paper text-xs font-bold font-courier px-2 py-0.5 rounded">
              {inconsistencies.length} Flagged
            </span>
          )}
        </h4>

        {inconsistencies.length === 0 ? (
          <div className="border border-stamp-green/20 bg-stamp-green/5 p-4 rounded text-sm font-grotesk text-center">
            No character inconsistencies flagged. All characters act in accordance with established traits.
          </div>
        ) : (
          <div className="space-y-3">
            {inconsistencies.map((inc, index) => {
              const isMajor = inc.severity === "major";

              return (
                <div
                  key={index}
                  className={`border p-4 rounded bg-paper/50 ${
                    isMajor ? "border-red-flag/40 bg-red-flag/5" : "border-ink/15"
                  }`}
                >
                  <div className="flex items-center gap-2 border-b border-ink/10 pb-2 mb-2">
                    <AlertTriangle size={16} className={isMajor ? "text-red-flag" : "text-ink/80"} />
                    <span className="font-bold text-sm text-ink uppercase">{inc.character}</span>
                    <span
                      className={`text-xs font-bold font-courier uppercase px-2 py-0.5 rounded ml-auto ${
                        isMajor ? "bg-red-flag text-paper" : "bg-ink/10 text-ink"
                      }`}
                    >
                      {inc.severity} Inconsistency
                    </span>
                  </div>

                  <div className="space-y-2 text-sm font-grotesk">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                      <div className="p-2 border border-ink/10 bg-paper rounded">
                        <div className="font-bold opacity-60 uppercase mb-0.5">Established Trait</div>
                        <div className="font-courier opacity-95">{inc.established_trait}</div>
                      </div>
                      <div className="p-2 border border-ink/10 bg-paper rounded">
                        <div className="font-bold opacity-60 uppercase mb-0.5">Contradicting Action</div>
                        <div className="font-courier text-red-flag font-semibold">{inc.contradicting_action}</div>
                      </div>
                    </div>

                    <div className="mt-2 text-sm">
                      <span className="font-bold text-xs opacity-60 uppercase">Description: </span>
                      <span className="opacity-95">{inc.description}</span>
                    </div>

                    <div className="text-right text-xs font-courier text-ink/75">
                      Contradiction occurs on <span className="underline font-bold">Page {inc.page || "Unknown"}</span>
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
