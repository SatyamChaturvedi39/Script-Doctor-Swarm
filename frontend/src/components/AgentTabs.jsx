import React, { useState } from "react";
import StructureDetail from "./StructureDetail";
import CharacterDetail from "./CharacterDetail";
import CompsDetail from "./CompsDetail";
import ContinuityDetail from "./ContinuityDetail";

export default function AgentTabs({ report }) {
  const [activeTab, setActiveTab] = useState("structure");

  const tabs = [
    {
      id: "structure",
      label: "STRUCTURE",
      colorClass: "bg-carbon-blue text-paper border-carbon-blue",
      borderClass: "border-carbon-blue",
      inactiveClass: "bg-carbon-blue/20 text-carbon-blue hover:bg-carbon-blue/35 border-carbon-blue/20",
      content: <StructureDetail detail={report.structure_detail} />,
    },
    {
      id: "character",
      label: "CHARACTER",
      colorClass: "bg-ink text-paper border-ink",
      borderClass: "border-ink",
      inactiveClass: "bg-ink/10 text-ink hover:bg-ink/20 border-ink/20",
      content: <CharacterDetail detail={report.character_detail} />,
    },
    {
      id: "comps",
      label: "COMPS & MARKET",
      colorClass: "bg-manila text-ink border-manila",
      borderClass: "border-manila",
      inactiveClass: "bg-manila/20 text-ink hover:bg-manila/30 border-manila/30",
      content: <CompsDetail detail={report.comps_detail} />,
    },
    {
      id: "continuity",
      label: "CONTINUITY",
      colorClass: "bg-red-flag text-paper border-red-flag",
      borderClass: "border-red-flag",
      inactiveClass: "bg-red-flag/15 text-red-flag hover:bg-red-flag/25 border-red-flag/25",
      content: <ContinuityDetail detail={report.continuity_detail} />,
    },
  ];

  const activeTabObj = tabs.find((t) => t.id === activeTab) || tabs[0];

  return (
    <div className="w-full mt-12 font-grotesk">
      {/* Labeled Folder Tabs Metaphor */}
      <div className="flex flex-wrap gap-1 border-b-2 border-ink">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-2.5 rounded-t-lg font-bold text-xs md:text-sm border-t border-x transition-all duration-150 uppercase tracking-wider relative -mb-[2px] z-10 ${
                isActive
                  ? `${tab.colorClass} border-b-paper border-b-[2px] translate-y-[-1px]`
                  : `${tab.inactiveClass} border-b-ink`
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Main folder envelope contents */}
      <div className="bg-paper border-x border-b border-ink rounded-b-lg p-6 md:p-8 shadow-sm">
        {activeTabObj.content}
      </div>
    </div>
  );
}
