"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, MicOff } from "lucide-react";
import { documents, DocumentItem } from "@/lib/api";

type ChatTurn = {
  role: "user" | "assistant";
  content: string;
  sources?: { filename: string }[];
  provider?: string;
  streaming?: boolean;
};

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

const statusColor: Record<string, string> = {
  ready: "text-mint",
  processing: "text-amber",
  failed: "text-coral",
};

declare global {
  interface Window {
    SpeechRecognition?: any;
    webkitSpeechRecognition?: any;
  }
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [chat, setChat] = useState<ChatTurn[]>([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [listening, setListening] = useState(false);
  const sessionId = useRef(`session-${Date.now()}`);
  const fileInput = useRef<HTMLInputElement>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);

  function loadDocs() {
    documents.list().then((res) => setDocs(res.data));
  }

  useEffect(() => {
    loadDocs();
    const interval = setInterval(loadDocs, 4000); // pick up background processing status
    return () => clearInterval(interval);
  }, []);

  const speechSupported =
    typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);

  function toggleVoiceInput() {
    if (!speechSupported) return;

    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setQuestion((q) => (q ? `${q} ${transcript}` : transcript));
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await documents.upload(file);
      loadDocs();
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || asking) return;
    const userMessage = question;
    setChat((c) => [...c, { role: "user", content: userMessage }]);
    setQuestion("");
    setAsking(true);

    const token = typeof window !== "undefined" ? localStorage.getItem("flowmind_token") : null;
    const workspaceId = typeof window !== "undefined" ? localStorage.getItem("flowmind_workspace_id") : null;

    try {
      const socket = new WebSocket(`${WS_URL}/api/documents/chat/stream`);
      socketRef.current = socket;
      let assistantIndex = -1;

      socket.onopen = () => {
        setChat((c) => {
          assistantIndex = c.length;
          return [...c, { role: "assistant", content: "", streaming: true }];
        });
        socket.send(JSON.stringify({ token, workspace_id: workspaceId, session_id: sessionId.current, message: userMessage }));
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.error) {
          setChat((c) => c.map((t, i) => (i === assistantIndex ? { ...t, content: "Sign in again to continue.", streaming: false } : t)));
          socket.close();
          setAsking(false);
          return;
        }
        if (data.token) {
          setChat((c) => c.map((t, i) => (i === assistantIndex ? { ...t, content: t.content + data.token } : t)));
        }
        if (data.done) {
          setChat((c) => c.map((t, i) => (i === assistantIndex ? { ...t, streaming: false, provider: data.ai_provider, sources: data.sources } : t)));
          socket.close();
          setAsking(false);
        }
      };

      socket.onerror = async () => {
        // Fall back to the plain REST endpoint if the WebSocket can't connect
        const res = await documents.chat({ session_id: sessionId.current, message: userMessage });
        setChat((c) => [
          ...c.slice(0, assistantIndex >= 0 ? assistantIndex : c.length),
          { role: "assistant", content: res.data.reply, sources: res.data.sources, provider: res.data.ai_provider },
        ]);
        setAsking(false);
      };
    } catch {
      setAsking(false);
    }
  }

  return (
    <div className="grid md:grid-cols-2 gap-8">
      <div>
        <h1 className="font-display text-3xl text-ink mb-1">Documents</h1>
        <p className="text-slatetext mb-6">Upload files or images - both get indexed for search and Q&A.</p>

        <label className="btn-primary inline-block cursor-pointer mb-6">
          {uploading ? "Uploading..." : "Upload document or image"}
          <input
            ref={fileInput}
            type="file"
            className="hidden"
            onChange={handleUpload}
            accept=".pdf,.txt,.md,.csv,.png,.jpg,.jpeg,.webp,.gif"
          />
        </label>

        <div className="space-y-3">
          {docs.map((d) => (
            <div key={d.id} className="card p-4 flex justify-between items-start">
              <div>
                <p className="text-ink font-medium">{d.filename}</p>
                <p className="text-sm">
                  <span className="text-slatetext">{d.chunk_count} chunks - </span>
                  <span className={statusColor[d.status] || "text-slatetext"}>{d.status}</span>
                </p>
                {d.summary && <p className="text-sm text-slatetext mt-1 line-clamp-2">{d.summary}</p>}
              </div>
              <button onClick={() => documents.remove(d.id).then(loadDocs)} className="text-sm text-coral">
                Remove
              </button>
            </div>
          ))}
          {docs.length === 0 && <p className="text-slatetext text-sm">No documents yet.</p>}
        </div>
      </div>

      <div className="card p-5 flex flex-col h-[70vh]">
        <h2 className="font-medium text-ink mb-3">Ask your documents</h2>
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {chat.map((turn, i) => (
            <div key={i} className={turn.role === "user" ? "text-right" : "text-left"}>
              <p
                className={`inline-block px-3 py-2 rounded-md text-sm max-w-[85%] ${
                  turn.role === "user" ? "bg-violet text-white" : "bg-mist text-ink"
                }`}
              >
                {turn.content}
                {turn.streaming && <span className="animate-pulse">▍</span>}
              </p>
              {turn.provider && (
                <p className="text-xs text-slatetext mt-1">
                  via {turn.provider}
                  {turn.sources && turn.sources.length > 0 && <> - Sources: {turn.sources.map((s) => s.filename).join(", ")}</>}
                </p>
              )}
            </div>
          ))}
          {chat.length === 0 && <p className="text-slatetext text-sm">Upload a document, then ask a question about it.</p>}
        </div>
        <form onSubmit={handleAsk} className="flex gap-2">
          <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question, or use the mic..." />
          {speechSupported && (
            <button
              type="button"
              onClick={toggleVoiceInput}
              className={`shrink-0 rounded-md px-3 border ${listening ? "border-coral text-coral" : "border-mist text-slatetext"}`}
              title="Voice input"
            >
              {listening ? <MicOff size={16} /> : <Mic size={16} />}
            </button>
          )}
          <button type="submit" disabled={asking} className="btn-primary shrink-0">
            {asking ? "..." : "Ask"}
          </button>
        </form>
      </div>
    </div>
  );
}
