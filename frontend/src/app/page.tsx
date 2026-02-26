"use client";

import { useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { IngestPanel } from "@/components/IngestPanel";
import { DocumentsPanel } from "@/components/DocumentsPanel";

type Tab = "chat" | "ingest" | "docs";

function TabButton({
  tab,
  current,
  label,
  onClick,
}: {
  tab: Tab;
  current: Tab;
  label: string;
  onClick: (t: Tab) => void;
}) {
  const active = tab === current;

  return (
    <button
      onClick={() => onClick(tab)}
      className={[
        "px-4 py-2 rounded-full text-sm font-medium transition-all",
        active
          ? "bg-blue-600 text-white shadow"
          : "bg-slate-100 text-slate-700 hover:bg-slate-200",
      ].join(" ")}
    >
      {label}
    </button>
  );
}

export default function Page() {
  const [tab, setTab] = useState<Tab>("chat");

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top shell */}
      <div className="mx-auto max-w-6xl px-6 py-8">
        {/* Card */}
        <div className="rounded-3xl bg-white shadow-lg ring-1 ring-slate-200">
          {/* Tabs */}
          <div className="flex gap-2 border-b border-slate-200 px-6 py-4">
            <TabButton tab="chat" current={tab} label="Chat" onClick={setTab} />
            <TabButton tab="ingest" current={tab} label="Ingest" onClick={setTab} />
            <TabButton tab="docs" current={tab} label="Documents" onClick={setTab} />
          </div>

          {/* Content */}
          <div className="p-6">
            {tab === "chat" && <ChatPanel />}
            {tab === "ingest" && <IngestPanel />}
            {tab === "docs" && <DocumentsPanel />}
          </div>
        </div>
      </div>
    </div>
  );
}