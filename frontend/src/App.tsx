import { memo, useCallback, useEffect, useMemo, useState } from "react";
import {
  consumeSse,
  copyText,
  downloadText,
  exportTranscript,
  fetchHistory,
  fetchModels,
  fetchTranscript,
  formatDuration,
  formatTimestamp,
  generatePrompt,
  summarizeTranscript,
} from "./api";
import { Button, Panel, ProgressBar, Select, TextArea } from "./components/ui";
import {
  PROMPT_TEMPLATE_LABELS,
  TARGET_LANGUAGES,
  type HistoryItem,
  type PromptTemplate,
  type TranscriptResult,
} from "./types";

function readClipboardPayload(data: DataTransfer | ClipboardEvent["clipboardData"]): {
  text: string;
  types: string[];
} {
  if (!data) return { text: "", types: [] };

  const types = Array.from(data.types);
  for (const type of types) {
    const value = data.getData(type);
    if (value?.trim()) {
      return { text: value.trim(), types };
    }
  }
  return { text: "", types };
}

const UrlInput = memo(function UrlInput({
  value,
  onChange,
  onPasteDebug,
  onClipboardBlocked,
}: {
  value: string;
  onChange: (value: string) => void;
  onPasteDebug: (detail: { length: number; via: string; types?: string[] }) => void;
  onClipboardBlocked: () => void;
}) {
  const applyText = (text: string, via: string, types: string[] = []) => {
    onPasteDebug({ length: text.length, via, types });
    if (text.trim()) {
      onChange(text.trim());
      return;
    }
    onClipboardBlocked();
  };

  return (
    <div
      className="flex-1"
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        const { text, types } = readClipboardPayload(event.dataTransfer);
        applyText(text, "drop", types);
      }}
    >
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onPaste={(event) => {
          const { text, types } = readClipboardPayload(event.clipboardData);
          applyText(text, "onPaste", types);
          if (text.trim()) {
            event.preventDefault();
            onChange(text.trim());
          }
        }}
        onFocus={() => {
          // #region agent log
          fetch("http://127.0.0.1:7411/ingest/8cd63242-fec5-4595-923c-95a8f6e64e61", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "8ea3a7" },
            body: JSON.stringify({
              sessionId: "8ea3a7",
              location: "App.tsx:urlFocus",
              message: "URL input focused",
              data: { valueLength: value.length },
              hypothesisId: "H1",
              timestamp: Date.now(),
            }),
          }).catch(() => {});
          // #endregion
        }}
        placeholder="https://www.youtube.com/watch?v=..."
        className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-indigo-400"
        autoComplete="off"
        spellCheck={false}
      />
    </div>
  );
});

function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [progressMessage, setProgressMessage] = useState("");
  const [progressPercent, setProgressPercent] = useState(0);
  const [error, setError] = useState("");
  const [transcript, setTranscript] = useState<TranscriptResult | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState("qwen2.5:14b");
  const [targetLanguage, setTargetLanguage] = useState("Turkish");
  const [tone, setTone] = useState<"formal" | "casual">("formal");
  const [translation, setTranslation] = useState("");
  const [translating, setTranslating] = useState(false);
  const [summary, setSummary] = useState("");
  const [summarizing, setSummarizing] = useState(false);
  const [promptTemplate, setPromptTemplate] = useState<PromptTemplate>("detailed_notes");
  const [generatedPrompt, setGeneratedPrompt] = useState("");
  const [promptLanguage, setPromptLanguage] = useState("Turkish");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [copied, setCopied] = useState("");
  const [clipboardBlocked, setClipboardBlocked] = useState(false);
  const handleUrlChange = useCallback((next: string) => {
    // #region agent log
    fetch("http://127.0.0.1:7411/ingest/8cd63242-fec5-4595-923c-95a8f6e64e61", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "8ea3a7" },
      body: JSON.stringify({
        sessionId: "8ea3a7",
        location: "App.tsx:urlChange",
        message: "URL input changed",
        data: { length: next.length },
        hypothesisId: "H2",
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    setUrl(next);
    if (next.trim()) {
      setClipboardBlocked(false);
    }
  }, []);

  const handlePasteDebug = useCallback((detail: { length: number; via: string; types?: string[] }) => {
    // #region agent log
    fetch("http://127.0.0.1:7411/ingest/8cd63242-fec5-4595-923c-95a8f6e64e61", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "8ea3a7" },
      body: JSON.stringify({
        sessionId: "8ea3a7",
        location: "App.tsx:urlPaste",
        message: "URL paste event",
        data: detail,
        hypothesisId: "H4",
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
  }, []);

  async function handlePasteFromClipboard() {
    try {
      const text = await navigator.clipboard.readText();
      handlePasteDebug({ length: text.length, via: "clipboardApi" });
      if (text.trim()) {
        handleUrlChange(text.trim());
        setClipboardBlocked(false);
        return;
      }
      setClipboardBlocked(true);
      setError(
        "Pano erişilemiyor veya boş. URL'yi aşağıdaki kutuya yazın, sürükleyip bırakın veya Chrome/Edge'de http://localhost:5173 açın.",
      );
    } catch (err) {
      // #region agent log
      fetch("http://127.0.0.1:7411/ingest/8cd63242-fec5-4595-923c-95a8f6e64e61", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "8ea3a7" },
        body: JSON.stringify({
          sessionId: "8ea3a7",
          location: "App.tsx:clipboardFail",
          message: "clipboard.readText failed",
          data: { error: err instanceof Error ? err.message : "unknown" },
          hypothesisId: "H4",
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      setError("Panodan yapıştırılamadı. URL'yi aşağıdaki kutuya yazın veya Chrome/Edge'de http://localhost:5173 açın.");
      setClipboardBlocked(true);
    }
  }

  const handleClipboardBlocked = useCallback(() => {
    setClipboardBlocked(true);
    setError(
      "Bu tarayıcı pano erişimini engelliyor. URL'yi aşağıdaki kutuya yazın, sürükleyip bırakın veya Chrome/Edge'de http://localhost:5173 açın.",
    );
  }, []);

  useEffect(() => {
    if (!loading) return;
    // #region agent log
    fetch("http://127.0.0.1:7411/ingest/8cd63242-fec5-4595-923c-95a8f6e64e61", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "8ea3a7" },
      body: JSON.stringify({
        sessionId: "8ea3a7",
        location: "App.tsx:loadingState",
        message: "loading active",
        data: { progressPercent, progressMessage },
        hypothesisId: "H3",
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
  }, [loading, progressPercent, progressMessage]);

  useEffect(() => {
    void bootstrap();
  }, []);

  async function bootstrap() {
    try {
      const [modelList, historyList] = await Promise.all([fetchModels(), fetchHistory()]);
      const names = modelList.map((item) => item.name);
      setModels(names);
      if (names.includes("qwen2.5:14b")) setSelectedModel("qwen2.5:14b");
      else if (names.includes("qwen2.5:32b")) setSelectedModel("qwen2.5:32b");
      else {
        const qwen = names.find((name) => name.toLowerCase().includes("qwen"));
        if (qwen) setSelectedModel(qwen);
        else if (names[0]) setSelectedModel(names[0]);
      }
      setHistory(historyList);
    } catch {
      setModels([]);
    }
  }

  const filteredSegments = useMemo(() => {
    if (!transcript) return [];
    const query = searchQuery.trim().toLowerCase();
    if (!query) return transcript.segments;
    return transcript.segments.filter((segment) =>
      segment.text.toLowerCase().includes(query),
    );
  }, [transcript, searchQuery]);

  async function handleTranscribe() {
    if (!url.trim()) return;
    setLoading(true);
    setError("");
    setProgressMessage("Başlatılıyor...");
    setProgressPercent(0.02);
    setTranscript(null);
    setTranslation("");
    setSummary("");
    setGeneratedPrompt("");

    try {
      await consumeSse<TranscriptResult>(
        "/api/transcribe",
        { url: url.trim() },
        {
          onProgress: (payload) => {
            setProgressMessage(payload.message);
            if (typeof payload.progress === "number") {
              setProgressPercent(payload.progress);
            }
          },
          onComplete: (payload) => {
            setProgressPercent(1);
            setProgressMessage("Tamamlandı.");
            setTranscript(payload);
            void bootstrap();
          },
          onError: (message) => setError(message),
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transkript oluşturulamadı.");
    } finally {
      setLoading(false);
      setTimeout(() => {
        setProgressMessage("");
        setProgressPercent(0);
      }, 1200);
    }
  }

  async function handleTranslate() {
    if (!transcript) return;
    setTranslating(true);
    setTranslation("");
    setError("");

    try {
      await consumeSse<{ text: string }>(
        "/api/translate",
        {
          transcript_id: transcript.id,
          target_language: targetLanguage,
          model: selectedModel,
          tone,
        },
        {
          onToken: (token) => setTranslation((prev) => prev + token),
          onComplete: (payload) => setTranslation(payload.text),
          onError: (message) => setError(message),
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Çeviri başarısız.");
    } finally {
      setTranslating(false);
    }
  }

  async function handleSummarize() {
    if (!transcript) return;
    setSummarizing(true);
    setSummary("");
    setError("");

    try {
      const result = await summarizeTranscript({
        transcript_id: transcript.id,
        model: selectedModel,
        language: targetLanguage,
      });
      setSummary(result.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Özet oluşturulamadı.");
    } finally {
      setSummarizing(false);
    }
  }

  async function handleGeneratePrompt() {
    if (!transcript) return;
    setError("");
    try {
      const result = await generatePrompt({
        transcript_id: transcript.id,
        template: promptTemplate,
        language: promptLanguage,
      });
      setGeneratedPrompt(result.prompt);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prompt oluşturulamadı.");
    }
  }

  async function handleLoadHistory(id: number) {
    setError("");
    try {
      const item = await fetchTranscript(id);
      setTranscript(item);
      setUrl(item.url);
      setTranslation("");
      setSummary("");
      setGeneratedPrompt("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kayıt yüklenemedi.");
    }
  }

  async function handleExport(format: "txt" | "srt" | "vtt") {
    if (!transcript) return;
    const result = await exportTranscript(transcript.id, format);
    downloadText(result.filename, result.content);
  }

  async function handleCopy(label: string, text: string) {
    await copyText(text);
    setCopied(label);
    setTimeout(() => setCopied(""), 1500);
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <header className="mb-8">
        <p className="text-sm uppercase tracking-[0.2em] text-indigo-300">Local AI</p>
        <h1 className="mt-2 text-4xl font-bold text-white">YouTube Transkript ve Çeviri</h1>
        <p className="mt-2 max-w-3xl text-slate-400">
          YouTube URL gir, Whisper ile transkript oluştur, Ollama ile çevir ve dış AI araçları için hazır prompt üret.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-6">
          <Panel title="Video URL">
            <div className="flex flex-col gap-3 md:flex-row">
              <UrlInput
                value={url}
                onChange={handleUrlChange}
                onPasteDebug={handlePasteDebug}
                onClipboardBlocked={handleClipboardBlocked}
              />
              <Button variant="secondary" onClick={handlePasteFromClipboard}>
                Yapıştır
              </Button>
              <Button onClick={handleTranscribe} disabled={loading || !url.trim()}>
                {loading ? "İşleniyor..." : "Transkript Oluştur"}
              </Button>
            </div>
            {clipboardBlocked && (
              <div className="mt-3 space-y-2">
                <p className="text-sm text-amber-300">
                  Pano engelli — URL&apos;yi buraya yazın veya adres çubuğundan sürükleyip bırakın.
                  Chrome/Edge: http://localhost:5173
                </p>
                <TextArea
                  value={url}
                  onChange={handleUrlChange}
                  rows={2}
                  placeholder="YouTube URL'sini buraya yazın..."
                />
              </div>
            )}
            {(loading || progressMessage) && (
              <ProgressBar
                value={progressPercent}
                label={progressMessage || "İşleniyor..."}
              />
            )}
            {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}
          </Panel>

          {transcript && (
            <>
              <Panel title={transcript.title}>
                <div className="mb-4 flex flex-wrap gap-3 text-sm text-slate-400">
                  <span>Dil: {transcript.language ?? "-"}</span>
                  <span>Süre: {formatDuration(transcript.duration)}</span>
                  <span>Segment: {transcript.segments.length}</span>
                </div>

                <input
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Transkript içinde ara..."
                  className="mb-4 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-indigo-400"
                />

                <div className="max-h-[420px] space-y-3 overflow-y-auto pr-2">
                  {filteredSegments.map((segment, index) => (
                    <div
                      key={`${segment.start}-${index}`}
                      className="rounded-xl border border-slate-800 bg-slate-950/70 p-3"
                    >
                      <div className="mb-1 text-xs text-indigo-300">
                        {formatTimestamp(segment.start)} - {formatTimestamp(segment.end)}
                      </div>
                      <p className="text-sm leading-6 text-slate-200">{segment.text}</p>
                    </div>
                  ))}
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Button variant="secondary" onClick={() => handleCopy("transcript", transcript.full_text)}>
                    {copied === "transcript" ? "Kopyalandı" : "Transkripti Kopyala"}
                  </Button>
                  <Button variant="ghost" onClick={() => handleExport("txt")}>TXT</Button>
                  <Button variant="ghost" onClick={() => handleExport("srt")}>SRT</Button>
                  <Button variant="ghost" onClick={() => handleExport("vtt")}>VTT</Button>
                </div>
              </Panel>

              <div className="grid gap-6 xl:grid-cols-2">
                <Panel title="Çeviri">
                  <div className="mb-3 grid gap-3 md:grid-cols-2">
                    <Select value={targetLanguage} onChange={setTargetLanguage}>
                      {TARGET_LANGUAGES.map((language) => (
                        <option key={language} value={language}>{language}</option>
                      ))}
                    </Select>
                    <Select value={selectedModel} onChange={setSelectedModel}>
                      {models.length === 0 ? (
                        <option value={selectedModel}>{selectedModel}</option>
                      ) : (
                        models.map((model) => (
                          <option key={model} value={model}>{model}</option>
                        ))
                      )}
                    </Select>
                  </div>
                  <div className="mb-3">
                    <Select value={tone} onChange={(value) => setTone(value as "formal" | "casual")}>
                      <option value="formal">Resmi ton</option>
                      <option value="casual">Sade ton</option>
                    </Select>
                  </div>
                  <Button onClick={handleTranslate} disabled={translating}>
                    {translating ? "Çevriliyor..." : "Çevir"}
                  </Button>
                  <TextArea
                    className="mt-4"
                    value={translation}
                    readOnly
                    rows={12}
                    placeholder="Çeviri burada görünecek..."
                  />
                  {translation && (
                    <div className="mt-3">
                      <Button variant="secondary" onClick={() => handleCopy("translation", translation)}>
                        {copied === "translation" ? "Kopyalandı" : "Çeviriyi Kopyala"}
                      </Button>
                    </div>
                  )}
                </Panel>

                <Panel title="Özet">
                  <Button onClick={handleSummarize} disabled={summarizing}>
                    {summarizing ? "Özetleniyor..." : "Özetle"}
                  </Button>
                  <TextArea
                    className="mt-4"
                    value={summary}
                    readOnly
                    rows={12}
                    placeholder="Video özeti burada görünecek..."
                  />
                </Panel>
              </div>

              <Panel title="Prompt Oluştur">
                <div className="mb-3 grid gap-3 md:grid-cols-2">
                  <Select
                    value={promptTemplate}
                    onChange={(value) => setPromptTemplate(value as PromptTemplate)}
                  >
                    {Object.entries(PROMPT_TEMPLATE_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </Select>
                  <Select value={promptLanguage} onChange={setPromptLanguage}>
                    {TARGET_LANGUAGES.map((language) => (
                      <option key={language} value={language}>{language}</option>
                    ))}
                  </Select>
                </div>
                <Button onClick={handleGeneratePrompt}>Prompt Oluştur</Button>
                <TextArea
                  className="mt-4"
                  value={generatedPrompt}
                  readOnly
                  rows={14}
                  placeholder="Oluşturulan prompt burada görünecek..."
                />
                {generatedPrompt && (
                  <div className="mt-3">
                    <Button variant="secondary" onClick={() => handleCopy("prompt", generatedPrompt)}>
                      {copied === "prompt" ? "Kopyalandı" : "Promptu Kopyala"}
                    </Button>
                  </div>
                )}
              </Panel>
            </>
          )}
        </div>

        <Panel title="Geçmiş" className="h-fit">
          <div className="space-y-3">
            {history.length === 0 && (
              <p className="text-sm text-slate-400">Henüz kayıt yok.</p>
            )}
            {history.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => handleLoadHistory(item.id)}
                className="w-full rounded-xl border border-slate-800 bg-slate-950/70 p-3 text-left transition hover:border-indigo-400"
              >
                <p className="text-sm font-medium text-white">{item.title}</p>
                <p className="mt-1 text-xs text-slate-400">
                  {item.language ?? "-"} · {formatDuration(item.duration)} · {item.segment_count} segment
                </p>
              </button>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

export default App;
