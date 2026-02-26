"use client";

import { useState } from "react";
import { ingestAudio, ingestFile, ingestText, ingestUrl, jobStatus } from "@/lib/api";
import type { DocumentRow, IngestJobOut } from "@/lib/types";

export function IngestPanel() {
  const [mode, setMode] = useState<"text" | "url" | "file" | "audio">("text");
  const [title, setTitle] = useState("Daily Notes");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [createdDoc, setCreatedDoc] = useState<DocumentRow | null>(null);
  const [job, setJob] = useState<IngestJobOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onIngest() {
    setErr(null);
    setBusy(true);
    setCreatedDoc(null);
    setJob(null);

    try {
      let doc: DocumentRow;
      if (mode === "text") doc = await ingestText({ title, text });
      else if (mode === "url") doc = await ingestUrl({ title, url });
      else if (mode === "file") {
        if (!file) throw new Error("Pick a file first");
        doc = await ingestFile(file);
      } else {
        if (!file) throw new Error("Pick an audio file first");
        doc = await ingestAudio(file);
      }

      setCreatedDoc(doc);

      // poll once immediately
      const j = await jobStatus(doc.id);
      setJob(j);
    } catch (e: any) {
      setErr(e?.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onRefreshJob() {
    if (!createdDoc) return;
    setErr(null);
    try {
      const j = await jobStatus(createdDoc.id);
      setJob(j);
    } catch (e: any) {
      setErr(e?.message || String(e));
    }
  }

  return (
    <div className="grid gap-4">
      <div className="rounded-2xl border bg-white p-4">
        <div className="flex flex-wrap gap-2">
          {(["text", "url", "file", "audio"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={[
                "rounded-xl px-3 py-2 text-sm font-medium",
                mode === m ? "bg-zinc-900 text-white" : "bg-white text-zinc-800 border hover:bg-zinc-50"
              ].join(" ")}
            >
              {m.toUpperCase()}
            </button>
          ))}
        </div>

        <div className="mt-4 grid gap-3">
          <div className="grid gap-1">
            <label className="text-xs text-zinc-600">Title</label>
            <input
              className="rounded-xl border px-3 py-2 text-sm"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {mode === "text" && (
            <div className="grid gap-1">
              <label className="text-xs text-zinc-600">Text</label>
              <textarea
                className="min-h-[160px] rounded-xl border px-3 py-2 text-sm"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste notes here..."
              />
            </div>
          )}

          {mode === "url" && (
            <div className="grid gap-1">
              <label className="text-xs text-zinc-600">URL</label>
              <input
                className="rounded-xl border px-3 py-2 text-sm"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://..."
              />
            </div>
          )}

          {(mode === "file" || mode === "audio") && (
            <div className="grid gap-1">
              <label className="text-xs text-zinc-600">
                {mode === "audio" ? "Audio file" : "Document file"}
              </label>
              <input
                type="file"
                className="rounded-xl border bg-white px-3 py-2 text-sm"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <div className="text-xs text-zinc-500">
                Selected: {file?.name ?? "none"}
              </div>
            </div>
          )}

          {err && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{err}</div>}

          <div className="flex flex-wrap gap-2">
            <button
              disabled={busy}
              onClick={onIngest}
              className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {busy ? "Ingesting..." : "Ingest"}
            </button>
            <button
              disabled={!createdDoc}
              onClick={onRefreshJob}
              className="rounded-xl border bg-white px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              Refresh Job
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border bg-white p-4">
        <div className="font-medium">Latest result</div>

        {!createdDoc ? (
          <div className="mt-3 text-sm text-zinc-500">No ingestion yet.</div>
        ) : (
          <div className="mt-3 grid gap-2 text-sm">
            <div className="rounded-xl bg-zinc-50 p-3 border">
              <div><span className="text-zinc-500">Doc ID:</span> <b>{createdDoc.id}</b></div>
              <div><span className="text-zinc-500">Status:</span> <b>{createdDoc.status}</b></div>
              <div><span className="text-zinc-500">Type:</span> <b>{createdDoc.source_type}</b></div>
              <div className="truncate"><span className="text-zinc-500">Title:</span> <b>{createdDoc.title}</b></div>
            </div>

            {job && (
              <div className="rounded-xl bg-zinc-50 p-3 border">
                <div><span className="text-zinc-500">Job Status:</span> <b>{job.status}</b></div>
                <div><span className="text-zinc-500">Stage:</span> <b>{job.stage}</b></div>
                {job.error && <div className="mt-2 text-red-700"><b>Error:</b> {job.error}</div>}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}