import React from "react";
import VerdictStamp from "./VerdictStamp";
import AgentTabs from "./AgentTabs";
import { User, FileText, BarChart2, MessageSquare, AlertCircle } from "lucide-react";

export default function CoverageReport({ report, onReset }) {
  if (!report) return null;

  return (
    <div className="w-full max-w-4xl mx-auto mt-6 p-4">
      {/* Physical Coverage Folder / Sheet Container */}
      <div className="bg-paper border-2 border-ink shadow-lg p-6 md:p-10 relative text-left">
        {/* Decorative elements of reader copies */}
        <div className="absolute top-4 right-6 text-[10px] font-courier opacity-50 uppercase tracking-widest">
          CONFIDENTIAL // STUDIO COVERAGE REPORT
        </div>

        {/* Title / Heading */}
        <div className="border-b-2 border-ink pb-4 mb-6">
          <h1 className="font-courier font-bold text-3xl md:text-4xl text-ink uppercase tracking-tight m-0">
            Script Doctor Coverage
          </h1>
          <p className="font-grotesk text-xs opacity-60 uppercase tracking-widest mt-1">
            Automated Multi-Agent Screenplay Evaluation Swarm
          </p>
        </div>

        {/* 1. Header grid metadata fields */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2 border border-ink bg-paper/50 rounded mb-8 font-grotesk text-sm">
          <div className="p-3 border-b md:border-b-0 md:border-r border-ink">
            <span className="font-bold text-xs opacity-60 uppercase block">Screenplay Title</span>
            <span className="font-courier font-bold text-base text-ink uppercase">{report.title}</span>
          </div>
          <div className="p-3 border-b md:border-b-0 md:border-r border-ink">
            <span className="font-bold text-xs opacity-60 uppercase block">Writer(s)</span>
            <span className="font-courier font-bold text-base text-ink">{report.writer}</span>
          </div>
          <div className="p-3 border-b md:border-b-0 md:border-r border-ink">
            <span className="font-bold text-xs opacity-60 uppercase block">Genre</span>
            <span className="font-courier font-bold text-base text-ink uppercase">{report.genre}</span>
          </div>
          <div className="p-3">
            <span className="font-bold text-xs opacity-60 uppercase block">Page Count</span>
            <span className="font-courier font-bold text-base text-ink">{report.page_count} Pages</span>
          </div>
        </div>

        {/* 2. Primary evaluation layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main comments / sections (left 2/3 cols) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Logline */}
            <div className="border-l-4 border-ink pl-4 py-2 bg-ink/5 rounded-r">
              <span className="font-grotesk font-black text-xs uppercase text-ink/65 tracking-wider block mb-1">
                Logline
              </span>
              <p className="font-grotesk font-semibold text-sm italic text-ink leading-relaxed">
                "{report.logline}"
              </p>
            </div>

            {/* Synopsis */}
            <div className="space-y-2">
              <h3 className="font-grotesk font-black text-xs uppercase text-ink tracking-widest border-b border-ink/35 pb-1">
                SYNOPSIS
              </h3>
              <div className="font-courier text-sm leading-relaxed text-ink/90 whitespace-pre-line bg-paper/50 p-4 border border-ink/15 rounded max-h-[350px] overflow-y-auto">
                {report.synopsis}
              </div>
            </div>

            {/* Form Labeled Sections */}
            <div className="space-y-4 pt-4">
              <h3 className="font-grotesk font-black text-xs uppercase text-ink tracking-widest border-b border-ink/35 pb-1">
                READER ASSESSMENT COMMENTS
              </h3>

              {report.comments && Object.entries(report.comments).map(([cat, text]) => {
                if (!text) return null;
                return (
                  <div key={cat} className="space-y-1">
                    <span className="font-grotesk font-bold text-xs uppercase text-ink/80 block">
                      {cat} Assessment
                    </span>
                    <p className="text-sm text-ink/95 leading-relaxed font-grotesk bg-paper/20 border border-ink/10 p-3 rounded">
                      {text}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right sidebar: scorecard & verdict stamp (right 1/3 col) */}
          <div className="space-y-8 flex flex-col justify-start">
            {/* Verdict Stamp frame */}
            <div className="border-2 border-dashed border-ink p-4 rounded bg-paper/50 text-center relative flex flex-col items-center justify-center min-h-[160px]">
              <span className="font-grotesk font-bold text-[10px] opacity-60 uppercase tracking-widest absolute top-2">
                Official Reader Decision
              </span>
              <div className="mt-4">
                <VerdictStamp verdict={report.verdict} />
              </div>
              <p className="font-grotesk text-xs mt-3 opacity-70 leading-relaxed max-w-[220px]">
                {report.verdict_justification}
              </p>
            </div>

            {/* Scorecard ratings grid */}
            <div className="border border-ink rounded overflow-hidden shadow-sm">
              <div className="bg-ink text-paper text-xs uppercase font-bold p-3 tracking-wider font-grotesk">
                Evaluation Grid Scorecard
              </div>
              <div className="divide-y divide-ink/20 bg-paper/50">
                {report.scorecard && report.scorecard.map((item) => {
                  const isExcellent = item.rating === "Excellent";
                  const isPoor = item.rating === "Poor";

                  return (
                    <div key={item.category} className="flex justify-between items-center p-3 text-sm font-grotesk">
                      <span className="font-semibold text-ink/85">{item.category}</span>
                      <span
                        className={`font-courier font-bold text-xs px-2 py-0.5 rounded border ${
                          isExcellent
                            ? "bg-stamp-green/10 text-stamp-green border-stamp-green/20"
                            : isPoor
                            ? "bg-red-flag/10 text-red-flag border-red-flag/20"
                            : "bg-ink/5 text-ink border-ink/10"
                        }`}
                      >
                        {item.rating}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Reset / Upload button */}
            <button
              onClick={onReset}
              className="w-full py-3 border border-ink rounded font-grotesk font-bold text-sm bg-ink text-paper hover:bg-paper hover:text-ink active:translate-y-[1px] transition-all"
            >
              EVALUATE ANOTHER SCREENPLAY
            </button>
          </div>
        </div>

        {/* 3. Deep-dive detailed tabs */}
        <AgentTabs report={report} />
      </div>
    </div>
  );
}
