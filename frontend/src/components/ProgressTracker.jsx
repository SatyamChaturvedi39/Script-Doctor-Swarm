import React from "react";
import { Check, Flame, Clipboard } from "lucide-react";

export default function ProgressTracker({ events, status, error }) {
  // Determine states of the four agents
  const agentStates = {
    structure: { status: "waiting", message: "Awaiting initialization" },
    character: { status: "waiting", message: "Awaiting initialization" },
    comps: { status: "waiting", message: "Awaiting initialization" },
    continuity: { status: "waiting", message: "Awaiting initialization" },
    synthesizer: { status: "waiting", message: "Awaiting initialization" },
  };

  // Process events sequentially to update states
  events.forEach((evt) => {
    const agent = evt.agent;
    if (agent && agentStates[agent]) {
      if (evt.event === "agent_start") {
        agentStates[agent].status = "analyzing";
        agentStates[agent].message = evt.message || "Analyzing screenplay...";
      } else if (evt.event === "agent_complete") {
        agentStates[agent].status = "complete";
        agentStates[agent].message = evt.message || "Analysis complete.";
      } else if (evt.event === "agent_error") {
        agentStates[agent].status = "error";
        agentStates[agent].message = evt.message || "Failed.";
      } else if (evt.event === "complete" && agent === "synthesizer") {
        agentStates.synthesizer.status = "complete";
        agentStates.synthesizer.message = "Synthesis complete.";
      }
    }
  });

  const agentsList = [
    { key: "structure", label: "STRUCTURE AGENT (Save the Cat beats)", color: "text-carbon-blue border-carbon-blue" },
    { key: "character", label: "CHARACTER AGENT (Motivation & inconsistencies)", color: "text-ink border-ink" },
    { key: "comps", label: "COMPS AGENT (TMDB comparable retrieval)", color: "text-manila border-manila" },
    { key: "continuity", label: "CONTINUITY AGENT (Prop/timeline contradictions)", color: "text-red-flag border-red-flag" },
  ];

  return (
    <div className="w-full max-w-xl mx-auto mt-12 p-4 font-grotesk">
      {/* Tracker Frame Header */}
      <div className="flex">
        <div className="bg-ink text-paper px-6 py-2 rounded-t-lg font-bold text-sm border-t border-x border-ink relative z-10 select-none">
          SWARM RUNNING...
        </div>
        <div className="flex-1 border-b border-ink"></div>
      </div>

      {/* Manila/Paper styled ledger body */}
      <div className="bg-paper border border-ink rounded-b-lg rounded-tr-lg p-6 shadow-md relative">
        <div className="text-xs font-courier opacity-50 uppercase absolute top-4 right-4">
          Status: {status.toUpperCase()}
        </div>

        <h3 className="font-courier font-bold text-lg mb-6 border-b border-ink/30 pb-2 text-left uppercase">
          Orchestration Ledger
        </h3>

        {/* List of 4 analysis agents */}
        <div className="space-y-4">
          {agentsList.map((agent) => {
            const state = agentStates[agent.key];
            const isWaiting = state.status === "waiting";
            const isAnalyzing = state.status === "analyzing";
            const isComplete = state.status === "complete";
            const isError = state.status === "error";

            return (
              <div
                key={agent.key}
                className="flex items-center justify-between p-4 border border-ink/20 bg-paper/40 rounded transition-all"
              >
                <div className="flex-1 text-left">
                  <div className="font-bold text-sm text-ink">{agent.label}</div>
                  <div className="font-courier text-xs text-ink/70 mt-1">
                    {isWaiting && <span className="opacity-50">&#8250; Awaiting...</span>}
                    {isAnalyzing && (
                      <span className="text-ink animate-pulse">&#8250; {state.message}</span>
                    )}
                    {isComplete && (
                      <span className="text-ink font-bold">&#8250; {state.message}</span>
                    )}
                    {isError && (
                      <span className="text-red-flag font-bold">&#8250; {state.message}</span>
                    )}
                  </div>
                </div>

                {/* Stamped checkmark graphic instead of spinner */}
                <div className="w-12 h-12 flex items-center justify-center relative">
                  {isAnalyzing && (
                    <div className="w-4 h-4 rounded-full border-2 border-ink border-t-transparent animate-spin"></div>
                  )}

                  {isComplete && (
                    <div className={`transform rotate-[-12deg] border-2 px-2 py-0.5 rounded font-courier font-bold text-xs uppercase ${agent.color} select-none animate-[bounce_0.3s_ease-out]`}>
                      DONE
                    </div>
                  )}

                  {isError && (
                    <div className="transform rotate-[8deg] border-2 border-red-flag px-2 py-0.5 rounded font-courier font-bold text-xs text-red-flag uppercase select-none">
                      FAIL
                    </div>
                  )}

                  {isWaiting && (
                    <div className="w-2 h-2 rounded-full bg-ink/20"></div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Synthesizer status at the bottom */}
        {status === "running" && agentStates.structure.status === "complete" &&
          agentStates.character.status === "complete" &&
          agentStates.comps.status === "complete" &&
          agentStates.continuity.status === "complete" && (
            <div className="mt-6 p-3 bg-manila/20 border border-manila text-ink rounded text-sm text-left animate-pulse">
              <Clipboard className="inline-block mr-2" size={16} />
              <span className="font-courier font-bold">SYNTHESIZING REPORT:</span> Merging per-category findings...
            </div>
          )}

        {/* Error alert */}
        {error && (
          <div className="mt-6 p-4 bg-red-flag/10 border border-red-flag text-red-flag rounded text-sm text-left">
            <h4 className="font-bold mb-1">Pipeline Execution Failure</h4>
            <p className="font-courier text-xs">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
