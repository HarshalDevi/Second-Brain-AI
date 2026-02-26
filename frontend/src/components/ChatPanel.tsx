"use client";

import { useMemo, useState } from "react";
import type { ChunkRow } from "@/lib/types";
import { chatStream } from "@/lib/api";
import { CitationsPanel } from "@/components/CitationsPanel";

type Msg = { role: "user" | "assistant"; text: string };

export function ChatPanel() {
  const [query, setQuery] = useState("");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [citations, setCitations] = useState<ChunkRow[]>([]);
  const [streaming, setStreaming] = useState(true);
  const [busy, setBusy] = useState(false);

  const canSend = useMemo(
    () => query.trim().length > 0 && !busy,
    [query, busy]
  );

  async function onSend() {
    const q = query.trim();
    if (!q) return;

    setBusy(true);
    setQuery("");
    setMsgs((m) => [...m, { role: "user", text: q }]);

    let assistantText = "";
    setMsgs((m) => [...m, { role: "assistant", text: "" }]);

    await chatStream(
      { query: q, conversation_id: conversationId },
      {
        onMeta: (meta) => {
          if (meta?.conversation_id != null)
            setConversationId(meta.conversation_id);
          if (Array.isArray(meta?.citations))
            setCitations(meta.citations);
        },
        onToken: (tok) => {
  assistantText += tok.startsWith(" ") ? tok : " " + tok;
  setMsgs((m) => {
    const copy = [...m];
    copy[copy.length - 1] = {
      role: "assistant",
      text: assistantText.trim(),
    };
    return copy;
  });
},
        onDone: () => setBusy(false),
      }
    );
  }

  return (
    <div className="flex flex-col gap-4 min-h-[65vh]">
      {/* Top bar */}
      <div className="flex justify-between items-center text-sm text-slate-500">
        <div>
          Conversation:{" "}
          <span className="font-medium text-slate-900">
            {conversationId ?? "new"}
          </span>
        </div>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={streaming}
            onChange={(e) => setStreaming(e.target.checked)}
          />
          Stream
        </label>
      </div>

      {/* Chat area */}
      <div className="flex-1 rounded-2xl bg-sky-50 p-4 overflow-auto ring-1 ring-sky-100">
        <div className="flex flex-col gap-3">
          {msgs.length === 0 && (
            <div className="text-sm text-slate-500">
              Ask something after ingesting content.
            </div>
          )}

          {msgs.map((m, i) => (
            <div
              key={i}
              className={[
                "max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap",
                m.role === "user"
                  ? "ml-auto bg-indigo-600 text-white shadow"
                  : "mr-auto bg-white text-slate-800 shadow-sm ring-1 ring-slate-200",
              ].join(" ")}
            >
              {m.text || "…"}
            </div>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && canSend) onSend();
          }}
          placeholder="Ask your second brain…"
          className="flex-1 rounded-xl bg-white px-4 py-2 ring-1 ring-slate-300 focus:ring-2 focus:ring-indigo-500"
        />
        <button
          onClick={onSend}
          disabled={!canSend}
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Send
        </button>
      </div>

      {/* Citations */}
      <CitationsPanel citations={citations} />
    </div>
  );
}