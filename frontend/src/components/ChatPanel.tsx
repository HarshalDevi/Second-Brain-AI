"use client";

import { useMemo, useState } from "react";
import { ArrowUp, Loader2, MessageSquareText, RotateCcw, Sparkles } from "lucide-react";
import type { ChunkRow } from "@/lib/types";
import { chatStream } from "@/lib/api";
import { CitationsPanel } from "@/components/CitationsPanel";

type Msg = { role: "user" | "assistant"; text: string };

const examples = [
  "Summarize my latest ingested document",
  "What facts support this answer?",
  "Tell me about MS Dhoni",
];

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

export function ChatPanel() {
  const [query, setQuery] = useState("");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [citations, setCitations] = useState<ChunkRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const canSend = useMemo(
    () => query.trim().length > 0 && !busy,
    [query, busy]
  );

  async function sendPrompt(prompt: string) {
    const q = prompt.trim();
    if (!q || busy) return;

    setErr(null);
    setBusy(true);
    setQuery("");
    setCitations([]);
    setMsgs((m) => [...m, { role: "user", text: q }, { role: "assistant", text: "" }]);

    let assistantText = "";

    try {
      await chatStream(
        { query: q, conversation_id: conversationId },
        {
          onMeta: (meta) => {
            if (typeof meta === "string") return;

            if (meta?.conversation_id != null)
              setConversationId(meta.conversation_id);
            if (Array.isArray(meta?.citations))
              setCitations(meta.citations);
          },
          onToken: (tok) => {
            assistantText += tok;
            setMsgs((m) => {
              const copy = [...m];
              copy[copy.length - 1] = {
                role: "assistant",
                text: assistantText.trimStart(),
              };
              return copy;
            });
          },
          onDone: () => setBusy(false),
        }
      );
    } catch (error) {
      setErr(errorMessage(error));
      setBusy(false);
      setMsgs((m) => {
        const copy = [...m];
        if (copy[copy.length - 1]?.role === "assistant" && !copy[copy.length - 1].text) {
          copy.pop();
        }
        return copy;
      });
    }
  }

  function resetConversation() {
    setConversationId(null);
    setMsgs([]);
    setCitations([]);
    setErr(null);
    setQuery("");
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
      <section className="flex min-h-[720px] flex-col overflow-hidden rounded-2xl bg-white ring-1 ring-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700 ring-1 ring-cyan-100">
              <MessageSquareText className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-950">Knowledge chat</div>
              <div className="text-xs text-slate-500">
                Conversation {conversationId ?? "new"} / grounded by retrieved chunks
              </div>
            </div>
          </div>

          <button
            onClick={resetConversation}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 ring-1 ring-slate-200 hover:bg-slate-100"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            Reset
          </button>
        </div>

        <div className="flex-1 overflow-y-auto bg-slate-50/70 px-4 py-4">
          {msgs.length === 0 ? (
            <div className="flex min-h-[460px] flex-col items-center justify-center text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-cyan-700 shadow-sm ring-1 ring-slate-200">
                <Sparkles className="h-6 w-6" aria-hidden="true" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-slate-950">
                Ask your second brain
              </h3>
              <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                Ask a question after ingesting notes, URLs, files, or audio. Answers stream with sources so you can inspect the evidence.
              </p>
              <div className="mt-5 flex max-w-xl flex-wrap justify-center gap-2">
                {examples.map((item) => (
                  <button
                    key={item}
                    onClick={() => sendPrompt(item)}
                    className="rounded-full bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-slate-200 hover:bg-cyan-50 hover:text-cyan-800 hover:ring-cyan-200"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="grid gap-4">
              {msgs.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={[
                    "flex",
                    message.role === "user" ? "justify-end" : "justify-start",
                  ].join(" ")}
                >
                  <div
                    className={[
                      "max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm",
                      message.role === "user"
                        ? "bg-slate-950 text-white"
                        : "bg-white text-slate-800 ring-1 ring-slate-200",
                    ].join(" ")}
                  >
                    <div className="whitespace-pre-wrap break-words">
                      {message.text || (
                        <span className="inline-flex items-center gap-2 text-slate-400">
                          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                          Thinking
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {err && (
          <div className="border-t border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
            {err}
          </div>
        )}

        <form
          className="border-t border-slate-200 bg-white p-3"
          onSubmit={(event) => {
            event.preventDefault();
            if (canSend) sendPrompt(query);
          }}
        >
          <div className="flex items-end gap-2 rounded-2xl bg-slate-50 p-2 ring-1 ring-slate-200 focus-within:ring-2 focus-within:ring-cyan-500">
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey && canSend) {
                  event.preventDefault();
                  sendPrompt(query);
                }
              }}
              rows={1}
              placeholder="Ask a grounded question..."
              className="max-h-32 min-h-11 flex-1 resize-none bg-transparent px-2 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
            />
            <button
              type="submit"
              disabled={!canSend}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-cyan-600 text-white transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              aria-label="Send message"
            >
              {busy ? (
                <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
              ) : (
                <ArrowUp className="h-5 w-5" aria-hidden="true" />
              )}
            </button>
          </div>
        </form>
      </section>

      <CitationsPanel citations={citations} />
    </div>
  );
}