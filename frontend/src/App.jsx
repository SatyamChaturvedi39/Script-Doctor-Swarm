import React, { useState } from "react";
import UploadForm from "./components/UploadForm";
import ProgressTracker from "./components/ProgressTracker";
import CoverageReport from "./components/CoverageReport";
import { useSSE } from "./hooks/useSSE";

export default function App() {
  const [jobId, setJobId] = useState(null);
  const { events, status, report, error } = useSSE(jobId);

  const handleUploadSuccess = (id) => {
    setJobId(id);
  };

  const handleReset = () => {
    setJobId(null);
  };

  return (
    <div className="w-full min-h-screen bg-paper flex flex-col font-grotesk">
      {/* Navigation Header bar replicating a minimal folder header */}
      <header className="border-b border-ink/30 px-6 py-4 bg-paper/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer select-none" onClick={handleReset}>
            <span className="font-courier font-black text-xl text-ink uppercase tracking-wider">
              Script Doctor Swarm
            </span>
            <span className="text-[10px] font-courier font-bold bg-red-flag text-paper px-1.5 py-0.2 rounded transform rotate-[3deg]">
              READER v0.1
            </span>
          </div>

          <div className="hidden md:flex items-center gap-6 text-xs font-bold tracking-wider text-ink/75 uppercase">
            <a href="https://github.com/SatyamChaturvedi39/Script-Doctor-Swarm" target="_blank" rel="noopener noreferrer" className="hover:text-red-flag transition-colors">
              Repository
            </a>
            <span className="opacity-30">|</span>
            <span className="opacity-75">Multi-Agent Coverage Suite</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 pb-16 flex flex-col items-center justify-start">
        {/* Upload Form view */}
        {!jobId && (
          <div className="w-full max-w-4xl mx-auto text-center px-4">
            <div className="mt-16 mb-8 max-w-xl mx-auto">
              <h2 className="font-courier font-bold text-3xl md:text-4xl text-ink uppercase tracking-tight">
                Evaluate Screenplay structure & integrity
              </h2>
              <p className="font-grotesk text-sm opacity-80 mt-3 leading-relaxed">
                Upload your screenplay (.txt or .pdf). A swarm of 5 specialized LangGraph agents will analyze narrative beats, character arcs, TMDB comparables, and continuity, synthesizing a studio coverage verdict.
              </p>
            </div>

            <UploadForm onUploadSuccess={handleUploadSuccess} />
          </div>
        )}

        {/* Swarm processing progress tracker */}
        {jobId && status !== "complete" && (
          <div className="w-full px-4">
            <ProgressTracker events={events} status={status} error={error} />
          </div>
        )}

        {/* Synthesized coverage sheet */}
        {status === "complete" && report && (
          <div className="w-full animate-[fadeIn_0.5s_ease-out]">
            <CoverageReport report={report} onReset={handleReset} />
          </div>
        )}
      </main>

      {/* Minimal Footer */}
      <footer className="border-t border-ink/15 py-6 text-center text-xs text-ink/50 bg-paper/30">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <p>© {new Date().getFullYear()} Script Doctor Swarm. Built for professional script assessment.</p>
          <p className="font-courier">Ink: #1F1B16 // Paper: #F7F3E8</p>
        </div>
      </footer>
    </div>
  );
}
