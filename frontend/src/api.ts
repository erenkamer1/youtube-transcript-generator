import type {
  HistoryItem,
  OllamaModel,
  PromptTemplate,
  TranscriptResult,
} from "./types";

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "İstek başarısız oldu.");
  }
  return response.json() as Promise<T>;
}

export async function fetchModels(): Promise<OllamaModel[]> {
  return parseJson(await fetch("/api/models"));
}

export async function fetchHistory(): Promise<HistoryItem[]> {
  return parseJson(await fetch("/api/history"));
}

export async function fetchTranscript(id: number): Promise<TranscriptResult> {
  return parseJson(await fetch(`/api/transcripts/${id}`));
}

export async function generatePrompt(payload: {
  transcript_id?: number;
  text?: string;
  template: PromptTemplate;
  language: string;
}): Promise<{ template: string; prompt: string }> {
  return parseJson(
    await fetch("/api/generate-prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
}

export async function summarizeTranscript(payload: {
  transcript_id?: number;
  text?: string;
  model?: string;
  language: string;
}): Promise<{ summary: string }> {
  return parseJson(
    await fetch("/api/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
}

export async function exportTranscript(
  id: number,
  format: "txt" | "srt" | "vtt",
): Promise<{ filename: string; content: string }> {
  return parseJson(await fetch(`/api/export/${id}/${format}`));
}

export async function consumeSse<TComplete>(
  url: string,
  body: unknown,
  handlers: {
    onProgress?: (payload: { stage: string; message: string; progress?: number }) => void;
    onToken?: (token: string) => void;
    onComplete: (payload: TComplete) => void;
    onError: (message: string) => void;
  },
): Promise<void> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok || !response.body) {
    throw new Error("Sunucu bağlantısı kurulamadı.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const lines = chunk.split("\n");
      const eventLine = lines.find((line) => line.startsWith("event:"));
      const dataLine = lines.find((line) => line.startsWith("data:"));
      if (!eventLine || !dataLine) continue;

      const event = eventLine.replace("event:", "").trim();
      const data = JSON.parse(dataLine.replace("data:", "").trim());

      if (event === "progress") {
        // #region agent log
        fetch("http://127.0.0.1:7411/ingest/8cd63242-fec5-4595-923c-95a8f6e64e61", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "8ea3a7" },
          body: JSON.stringify({
            sessionId: "8ea3a7",
            location: "api.ts:progress",
            message: "SSE progress received",
            data: { stage: data.stage, progress: data.progress },
            hypothesisId: "H1-H4",
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        handlers.onProgress?.(data);
      }
      if (event === "token") handlers.onToken?.(data.token);
      if (event === "complete") {
        // #region agent log
        fetch("http://127.0.0.1:7411/ingest/8cd63242-fec5-4595-923c-95a8f6e64e61", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "8ea3a7" },
          body: JSON.stringify({
            sessionId: "8ea3a7",
            location: "api.ts:complete",
            message: "SSE complete received",
            data: { id: data.id },
            hypothesisId: "H4",
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        handlers.onComplete(data);
      }
      if (event === "error") {
        // #region agent log
        fetch("http://127.0.0.1:7411/ingest/8cd63242-fec5-4595-923c-95a8f6e64e61", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "8ea3a7" },
          body: JSON.stringify({
            sessionId: "8ea3a7",
            location: "api.ts:error",
            message: "SSE error received",
            data: { message: data.message },
            hypothesisId: "H3-H4",
            timestamp: Date.now(),
          }),
        }).catch(() => {});
        // #endregion
        handlers.onError(data.message);
      }
    }
  }
}

export function formatDuration(seconds: number | null): string {
  if (!seconds) return "-";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

export function downloadText(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function copyText(text: string) {
  await navigator.clipboard.writeText(text);
}
