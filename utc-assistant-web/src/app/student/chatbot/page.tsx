"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Brain, Bot, FileText, MessageSquarePlus, Paperclip, Send, UserRound } from "lucide-react";
import { useAuth } from "@/components/shared/auth-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { apiChat, apiSuggestions } from "@/lib/api-client";
import { suggestedQuestions } from "@/lib/navigation";

type ChatMessage = {
  role: "student" | "bot";
  content: string;
  thinking?: string;
  thinkingDone?: boolean;
  messageId?: string;
  rated?: "up" | "down";
  sources?: Array<{
    title: string;
    heading: string;
    source_name: string;
    source_url?: string;
    type?: string;
    score: number;
    content: string;
  }>;
};

const welcome: ChatMessage = {
  role: "bot",
  content: "Xin chào, mình là Trợ lý ảo UTC. Bạn có thể hỏi về học phí, lịch thi, quy chế học vụ và thủ tục sinh viên.",
};

function sourceLabel(source: NonNullable<ChatMessage["sources"]>[number]) {
  if (source.type === "web") {
    try {
      const url = new URL(source.source_url || source.source_name);
      return url.hostname.replace(/^www\./, "");
    } catch {
      return source.source_name || source.title || "Nguồn web";
    }
  }
  return source.source_name || source.title || "Nguồn nội bộ";
}

export default function ChatbotPage() {
  const { token } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([welcome]);
  const [draft, setDraft] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState("");
  const [expandedSource, setExpandedSource] = useState<string | null>(null);
  const [topicSuggestions, setTopicSuggestions] = useState<string[]>([]);
  const [faqItems, setFaqItems] = useState<string[]>([]);
  const [conversations, setConversations] = useState<Array<{id:string,title:string}>>([]);
  const [activeConvId, setActiveConvId] = useState("");
  const endRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8001";

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    apiSuggestions()
      .then((res) => setTopicSuggestions(res.items))
      .catch(() => setTopicSuggestions(suggestedQuestions));
  }, []);

  useEffect(() => {
    if (!token) return;
    fetch(`${API_BASE}/api/faq`).then(r=>r.json()).then(d=>setFaqItems(d.items||[])).catch(()=>{});
    fetch(`${API_BASE}/api/conversations`,{headers:{Authorization:`Bearer ${token}`}})
      .then(r=>r.json()).then(d=>setConversations(d.items||[])).catch(()=>{});
  }, [token]);

  const newConversation = async () => {
    if (!token) return;
    const r = await fetch(`${API_BASE}/api/conversations`,{
      method:"POST",headers:{"Content-Type":"application/json",Authorization:`Bearer ${token}`},
      body:JSON.stringify({title:"Cuộc trò chuyện mới"}),
    });
    const d = await r.json();
    setActiveConvId(d.id);
    setConversations(prev=>[{id:d.id,title:d.title},...prev]);
    setMessages([welcome]);
  };

  const rateMessage = (msgIndex: number, rating: "up" | "down") => {
    const msg = messages[msgIndex];
    if (!msg.messageId || msg.rated) return;
    fetch(`${API_BASE}/api/feedback/rate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ message_id: msg.messageId, rating }),
    }).catch(() => {});
    setMessages(prev => {
      const updated = [...prev];
      updated[msgIndex] = { ...updated[msgIndex], rated: rating };
      return updated;
    });
  };

  const sendMessage = useCallback(
    async (raw?: string) => {
      const question = (raw ?? draft).trim();
      if (!question || !token || isTyping) return;
      setTimeout(() => setDraft(""), 0);
      setError("");
      setMessages((prev) => [...prev, { role: "student", content: question }]);
      setIsTyping(true);

      // Add placeholder bot message
      const botMsg: ChatMessage = { role: "bot", content: "", thinking: "", sources: [] };
      setMessages((prev) => [...prev, botMsg]);

      try {
        const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8001";
        // Auto-create conversation if none active
        let cid = activeConvId;
        if (!cid && token) {
          const r = await fetch(`${API_BASE}/api/conversations`,{
            method:"POST",headers:{"Content-Type":"application/json",Authorization:`Bearer ${token}`},
            body:JSON.stringify({title:question.slice(0,80)}),
          });
          const d = await r.json();
          cid = d.id;
          setActiveConvId(cid);
          setConversations(prev=>[{id:d.id,title:d.title},...prev]);
        }
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ question, top_k: 5, conversation_id: cid }),
        });

        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          throw new Error(err.detail || "Lỗi kết nối");
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("Không hỗ trợ streaming");
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event = JSON.parse(line.slice(6));
              setMessages((prev) => {
                const updated = [...prev];
                const last = { ...updated[updated.length - 1] };
                if (last.role !== "bot") return prev;

                switch (event.type) {
                  case "thinking":
                    last.thinking = (last.thinking || "") + event.content;
                    break;
                  case "answer":
                    last.content = ((last.content || "") + event.content).replace(/^\n+/, "");
                    last.thinkingDone = true;
                    break;
                  case "done":
                    last.sources = event.sources || [];
                    last.messageId = event.message_id || "";
                    break;
                  case "error":
                    last.content = last.content || "Lỗi: " + event.content;
                    break;
                }
                updated[updated.length - 1] = last;
                return updated;
              });
            } catch {
              // ignore parse errors
            }
          }
        }
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Không thể gửi câu hỏi.");
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "bot" && !last.content) {
            last.content = "Hệ thống chưa phản hồi được. Vui lòng thử lại sau.";
          }
          return updated;
        });
      } finally {
        setIsTyping(false);
      }
    },
    [draft, isTyping, token],
  );

  return (
    <div className="grid h-[calc(100vh-6.5rem)] min-h-[680px] gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
      <Card className="flex min-h-0 flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b bg-white px-5 py-4">
          <div>
            <p className="text-sm font-bold text-[#00828a]">Cổng sinh viên</p>
            <h1 className="mt-1 flex items-center gap-2 text-xl font-extrabold text-[#0f294a]">
              <Bot className="h-5 w-5" />
              Chatbot Trợ lý ảo UTC
            </h1>
          </div>
        </div>
        <ScrollArea className="flex-1 bg-slate-50">
          <div className="space-y-4 p-4 md:p-6">
            {messages.length === 1 ? (
              <div className="rounded-lg border border-dashed bg-white p-5">
                <p className="font-semibold text-slate-800">Câu hỏi thường gặp</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(faqItems.length > 0 ? faqItems : suggestedQuestions).slice(0,5).map((question) => (
                    <Button key={question} variant="outline" size="sm" onClick={() => void sendMessage(question)}>
                      {question}
                    </Button>
                  ))}
                </div>
              </div>
            ) : null}
            {messages.map((message, index) => {
              const isBot = message.role === "bot";
              return (
                <div key={`${message.role}-${index}`} className={isBot ? "flex justify-start" : "flex justify-end"}>
                  <div className={isBot ? "flex max-w-3xl gap-3" : "flex max-w-2xl flex-row-reverse gap-3"}>
                    <div className={isBot ? "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#0f294a] text-white" : "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#00828a] text-white"}>
                      {isBot ? <Bot className="h-4 w-4" /> : <UserRound className="h-4 w-4" />}
                    </div>
                    <div className={isBot ? "rounded-2xl rounded-tl-none border bg-white p-4 text-sm shadow-sm" : "rounded-2xl rounded-tr-none bg-[#0f294a] p-4 text-sm text-white shadow-sm"}>
                      <div className={isBot ? "ai-answer prose prose-sm max-w-none text-slate-700" : "prose prose-sm max-w-none text-white"}>
                        {isBot ? (
                          <div className="whitespace-pre-wrap font-mono text-xs leading-relaxed">
                            {message.content.trim()}
                          </div>
                        ) : (
                          <span>{message.content}</span>
                        )}
                      </div>
                      {isBot && (
                        <div className="mt-2 flex items-center gap-2 border-t pt-2">
                          <button onClick={() => rateMessage(index, "up")}
                            className={`text-xs px-2 py-1 rounded transition ${
                              message.rated === "up" ? "bg-green-100 text-green-700 font-medium" : "hover:bg-green-50 text-slate-400 hover:text-green-600"
                            }`}>
                            👍 {message.rated === "up" ? "Đã đánh giá" : "Hữu ích"}
                          </button>
                          <button onClick={() => rateMessage(index, "down")}
                            className={`text-xs px-2 py-1 rounded transition ${
                              message.rated === "down" ? "bg-red-100 text-red-700 font-medium" : "hover:bg-red-50 text-slate-400 hover:text-red-600"
                            }`}>
                            👎 {message.rated === "down" ? "Đã đánh giá" : "Không hữu ích"}
                          </button>
                        </div>
                      )}
                      {isBot && message.thinking ? (
                        !message.thinkingDone ? (
                          <div className="mt-2 rounded-md border-l-2 border-purple-400 bg-purple-50/50 px-3 py-2 text-xs leading-relaxed text-slate-500 whitespace-pre-wrap animate-pulse">
                            <span className="font-semibold text-purple-600">Đang suy luận...</span>
                            {"\n"}{message.thinking.trim()}
                          </div>
                        ) : (
                          <details className="mt-1 group">
                            <summary className="cursor-pointer text-[11px] font-medium text-purple-400 hover:text-purple-600 list-none">
                              <span className="inline-flex items-center gap-1">
                                <Brain className="h-3 w-3" />
                                Đã suy luận xong
                              </span>
                            </summary>
                            <div className="mt-1 rounded-md border-l-2 border-purple-200 bg-purple-50/20 px-3 py-2 text-xs leading-relaxed text-slate-500 whitespace-pre-wrap">
                              {message.thinking.trim()}
                            </div>
                          </details>
                        )
                      ) : null}
                      {isBot && message.sources?.length ? (
                        <div className="mt-3 border-t pt-3">
                          <div className="mb-2 flex items-center gap-1 text-xs font-bold text-slate-500">
                            <FileText className="h-4 w-4 text-primary" />
                            Nguồn trích dẫn
                          </div>
                          <div className="space-y-2">
                            {message.sources.map((source, sourceIndex) => {
                              const sourceKey = `${source.source_name}-${sourceIndex}`;
                              const isExpanded = expandedSource === sourceKey;
                              const isWebSource = source.type === "web";
                              const label = sourceLabel(source);
                              return (
                                <div key={sourceKey}>
                                  <button
                                    onClick={() => setExpandedSource(isExpanded ? null : sourceKey)}
                                    className={`w-full rounded-md border px-2.5 py-1.5 text-left text-xs transition ${
                                      isExpanded
                                        ? "border-primary bg-primary/5 text-primary"
                                        : "border-slate-200 bg-slate-50 text-slate-600 hover:border-primary/30 hover:bg-primary/5"
                                    }`}
                                  >
                                    <div className="flex items-center justify-between gap-2">
                                      <div className="min-w-0">
                                        <div className="flex items-center gap-2">
                                          <span
                                            className={`shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                                              isWebSource
                                                ? "bg-amber-100 text-amber-700"
                                                : "bg-slate-200 text-slate-700"
                                            }`}
                                          >
                                            {isWebSource ? "Nguồn web" : "Nguồn nội bộ"}
                                          </span>
                                          <span className="truncate font-medium">
                                            {label}
                                            {source.heading ? ` — ${source.heading}` : ""}
                                          </span>
                                        </div>
                                      </div>
                                      <span className="shrink-0 text-[10px] text-slate-400">
                                        {source.score != null ? `${(source.score * 100).toFixed(0)}%` : ""}
                                      </span>
                                    </div>
                                  </button>
                                  {isExpanded ? (
                                    <div className="mt-1.5 rounded-md border-l-2 border-[#f59e0b] bg-[#fef3c7] px-3 py-2 text-xs leading-relaxed text-[#1e293b]">
                                      {isWebSource && source.source_url ? (
                                        <div className="mb-2">
                                          <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-[#92400e]">
                                            Liên kết nguồn
                                          </div>
                                          <a
                                            href={source.source_url}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="break-all text-[11px] font-medium text-[#92400e] underline underline-offset-2"
                                          >
                                            {source.source_url}
                                          </a>
                                        </div>
                                      ) : null}
                                      {source.content ? (
                                        <>
                                      <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-[#92400e]">
                                        📌 Nội dung trích dẫn
                                      </div>
                                      {source.content.slice(0, 500)}
                                        </>
                                      ) : null}
                                    </div>
                                  ) : null}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
            {isTyping ? <div className="text-sm text-slate-500">Trợ lý đang soạn câu trả lời…</div> : null}
            {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</div> : null}
            <div ref={endRef} />
          </div>
        </ScrollArea>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (draft.trim() && !isTyping) {
              void sendMessage();
            }
          }}
          className="border-t bg-white p-4"
        >
          <div className="flex items-center gap-2 rounded-lg border bg-slate-50 p-2">
            <Button type="button" variant="ghost" size="icon" aria-label="Đính kèm tệp" disabled>
              <Paperclip className="h-5 w-5" />
            </Button>
            <Input
              ref={inputRef}
              className="border-0 bg-transparent shadow-none focus-visible:ring-1 rounded-none"
              placeholder={isTyping ? "Trợ lý đang trả lời..." : "Nhập câu hỏi của bạn..."}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              disabled={isTyping}
            />
            <Button type="submit" size="icon" aria-label="Gửi câu hỏi" disabled={!draft.trim() || !token || isTyping}>
              <Send className="h-5 w-5" />
            </Button>
          </div>
        </form>
      </Card>
      <aside className="hidden min-h-0 flex-col gap-3 xl:flex">
        <Button variant="outline" className="gap-2" onClick={newConversation}>
          <MessageSquarePlus className="h-4 w-4" />
          Cuộc trò chuyện mới
        </Button>
        <ScrollArea className="flex-1">
          <div className="space-y-1">
            {conversations.map(c => (
              <button key={c.id} onClick={() => setActiveConvId(c.id)}
              className={`w-full text-left px-3 py-2 text-sm rounded-md truncate ${
                c.id === activeConvId ? "bg-primary/10 text-primary font-medium" : "text-slate-600 hover:bg-slate-100"
              }`}>
              {c.title}
            </button>
          ))}
          </div>
        </ScrollArea>
      </aside>
    </div>
  );
}
