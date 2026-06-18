const logs = [
  ["2026-05-22 14:15:22", "INFO", "RAG-Retrieval-Service", "Retrieved 4 chunks for query học bổng K63."],
  ["2026-05-22 14:12:05", "INFO", "LLM-Gateway", "API call successful. Latency: 1.12s."],
  ["2026-05-22 14:05:10", "WARN", "Embedding-API", "Connection latency high on bge-m3 endpoint."],
  ["2026-05-22 13:58:44", "ERROR", "RAG-Ingestion-Pipeline", "File processing failed: CSV encoding error."],
];

export default function AdminLogsPage() {
  return (
    <div className="space-y-5">
      <div><p className="text-sm font-medium text-primary">Giám sát backend</p><h1 className="mt-1 text-2xl font-semibold">Nhật ký hệ thống</h1></div>
      <div className="overflow-hidden rounded-lg border bg-white">
        <div className="border-b bg-slate-50 px-5 py-4 text-xs font-bold uppercase text-slate-600">Hạ tầng hoạt động thực tế</div>
        <div className="max-h-[560px] overflow-y-auto bg-slate-950 p-4 font-mono text-[11px] leading-6 text-slate-300">
          {logs.map(([timestamp, level, service, message]) => (
            <div key={`${timestamp}-${service}`} className="grid gap-2 border-b border-slate-800 py-2 lg:grid-cols-[150px_72px_210px_minmax(0,1fr)]">
              <span className="text-slate-500">{timestamp}</span>
              <span className={level === "INFO" ? "font-bold text-emerald-400" : level === "WARN" ? "font-bold text-amber-400" : "font-bold text-rose-400"}>[{level}]</span>
              <span className="font-bold text-sky-400">[{service}]</span>
              <span>{message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
