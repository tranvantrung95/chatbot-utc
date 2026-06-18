"use client";

import { useState } from "react";
import { CheckCircle2, RefreshCw, Save, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function AdminConfigPage() {
  const [status, setStatus] = useState<"idle" | "testing" | "success">("idle");
  const [notice, setNotice] = useState("");

  return (
    <div className="space-y-5">
      <div><p className="text-sm font-medium text-primary">Điều khiển lõi</p><h1 className="mt-1 text-2xl font-semibold">Cấu hình RAG</h1></div>
      {notice ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{notice}</div> : null}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-white p-6">
          <h2 className="flex items-center gap-2 border-b pb-3 font-semibold"><Settings className="h-4 w-4 text-primary" />Kết nối mô hình</h2>
          {["vLLM API", "https://vllm.utc.edu.vn/v1", "qwen-2.5-72b-instruct-vietnamese", "bge-m3-vietnamese"].map((value) => <Input key={value} className="mt-4" defaultValue={value} />)}
        </div>
        <div className="rounded-lg border bg-white p-6">
          <h2 className="border-b pb-3 font-semibold">Chunking & Retrieval</h2>
          {[
            ["Chunk Size", 500, 100, 2000],
            ["Chunk Overlap", 50, 10, 500],
            ["Top-K", 4, 1, 10],
            ["Temperature", 0.1, 0, 1],
          ].map(([label, value, min, max]) => (
            <div key={label as string} className="mt-5">
              <div className="mb-1 flex justify-between text-sm"><span>{label}</span><span>{value}</span></div>
              <input type="range" min={min as number} max={max as number} step={label === "Temperature" ? 0.05 : 1} defaultValue={value as number} className="w-full accent-primary" />
            </div>
          ))}
          <div className="mt-6 flex gap-3">
            <Button variant="outline" onClick={() => { setStatus("testing"); window.setTimeout(() => setStatus("success"), 700); }}><RefreshCw className={`h-4 w-4 ${status === "testing" ? "animate-spin" : ""}`} />Kiểm tra</Button>
            <Button onClick={() => setNotice("Đã lưu cấu hình lõi RAG.")}><Save className="h-4 w-4" />Lưu</Button>
          </div>
          {status === "success" ? <div className="mt-4 flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700"><CheckCircle2 className="h-4 w-4" />Kết nối thành công.</div> : null}
        </div>
      </div>
    </div>
  );
}
