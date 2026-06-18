"use client";

import { useState } from "react";
import { FileText, RefreshCw, Save, UploadCloud } from "lucide-react";
import { useAuth } from "@/components/shared/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiImportDocument } from "@/lib/api-client";

export default function AdminImportPage() {
  const { token } = useAuth();
  const [fileName, setFileName] = useState("Quy_dinh_moi_phat_sinh_nam_2026.pdf");
  const [content, setContent] = useState("Nội dung mẫu dùng để kiểm thử pipeline RAG. Sinh viên cần tra cứu các quy định học vụ, lịch thi, học phí và thủ tục theo văn bản chính thức của Trường Đại học Giao thông Vận tải.");
  const [progress, setProgress] = useState<{ progress: number; step: string } | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const runPipeline = async () => {
    if (!token) return;
    setError("");
    setMessage("");
    const steps = [
      { progress: 25, step: "Đang đọc văn bản..." },
      { progress: 60, step: "Đang tách chunk..." },
      { progress: 90, step: "Đang sinh embedding..." },
      { progress: 100, step: "Chèn vào Vector DB thành công." },
    ];
    for (const step of steps) {
      setProgress(step);
      await new Promise((resolve) => window.setTimeout(resolve, 400));
    }
    try {
      await apiImportDocument(token, { title: fileName, source: "Import UI", content });
      setMessage("Đã nạp tài liệu thành công.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Backend chưa nhận tài liệu.");
    } finally {
      setProgress(null);
    }
  };

  return (
    <div className="space-y-5">
      <div><p className="text-sm font-medium text-primary">Pipeline tri thức</p><h1 className="mt-1 text-2xl font-semibold">Nạp tài liệu & tách chunks</h1></div>
      {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
      {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div> : null}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-white p-6">
          <div className="rounded-lg border-2 border-dashed bg-slate-50 p-8 text-center"><UploadCloud className="mx-auto mb-3 h-12 w-12 text-slate-400" /><p className="text-sm font-medium">Kéo thả tài liệu vào đây</p></div>
          <Input className="mt-4" value={fileName} onChange={(event) => setFileName(event.target.value)} />
          <Textarea className="mt-4 min-h-32" value={content} onChange={(event) => setContent(event.target.value)} />
          <Button className="mt-4 w-full" onClick={() => void runPipeline()}><Save className="h-4 w-4" /> Nạp vào Pipeline RAG</Button>
        </div>
        <div className="rounded-lg border bg-white p-6">
          <h2 className="font-semibold">Tiến trình</h2>
          {progress ? (
            <div className="mt-4 rounded-md border bg-slate-50 p-4">
              <div className="flex justify-between text-sm"><span>{fileName}</span><span>{progress.progress}%</span></div>
              <div className="mt-3 h-2 rounded-full bg-slate-200"><div className="h-full rounded-full bg-primary" style={{ width: `${progress.progress}%` }} /></div>
              <p className="mt-3 flex items-center gap-2 text-sm text-slate-500"><RefreshCw className="h-4 w-4 animate-spin" />{progress.step}</p>
            </div>
          ) : (
            <div className="mt-4 rounded-md border bg-slate-50 p-4 text-sm text-slate-500">Không có tiến trình đang chạy</div>
          )}
          <div className="mt-4 flex items-center gap-2 text-sm text-slate-600"><FileText className="h-4 w-4" /> Tệp gần đây sẽ hiển thị tại đây.</div>
        </div>
      </div>
    </div>
  );
}
