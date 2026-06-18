"use client";

import { useCallback, useEffect, useState } from "react";
import { Eye, FilePlus2, FileText, RefreshCw, Save, Search, Trash2, UploadCloud } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/components/shared/auth-provider";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { apiDocuments, apiImportDocument } from "@/lib/api-client";
import { StatusBadge, statusTone } from "@/components/shared/status-badge";

export default function AdminDocumentsPage() {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [documents, setDocuments] = useState<Array<{ id: string; name: string; type: string; source: string; status: string; updated_at: string; owner: string; chunk_count: number; char_count: number }>>([]);
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [content, setContent] = useState("");

  const loadDocuments = useCallback(async () => {
    if (!token) return;
    try {
      const response = await apiDocuments(token);
      setDocuments(response.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Không tải được tài liệu.");
    }
  }, [token]);

  useEffect(() => { void loadDocuments(); }, [loadDocuments]);

  const onImport = async () => {
    if (!token) return;
    if (content.trim().length < 50) {
      setError("Nội dung tài liệu cần tối thiểu 50 ký tự.");
      return;
    }
    setIsSaving(true);
    setError("");
    try {
      await apiImportDocument(token, { title: title.trim() || "Tài liệu import", source: source.trim() || "Nguồn nhập liệu", content: content.trim() });
      setOpen(false);
      setTitle("");
      setSource("");
      setContent("");
      await loadDocuments();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Không import được tài liệu.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-primary">Quản trị tri thức</p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-950">Kho dữ liệu & chỉ mục RAG</h1>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline"><Link href="/admin/import"><UploadCloud className="h-4 w-4" /> Pipeline import</Link></Button>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild><Button><FilePlus2 className="h-4 w-4" />Thêm tài liệu</Button></DialogTrigger>
            <DialogContent className="sm:max-w-2xl">
              <DialogHeader><DialogTitle>Nạp tài liệu vào kho RAG</DialogTitle><DialogDescription>Nhập nội dung văn bản để backend xử lý chunk.</DialogDescription></DialogHeader>
              <div className="space-y-4">
                <Input placeholder="Tên tài liệu" value={title} onChange={(event) => setTitle(event.target.value)} />
                <Input placeholder="Nguồn / đơn vị ban hành" value={source} onChange={(event) => setSource(event.target.value)} />
                <Textarea className="min-h-40" placeholder="Nội dung tài liệu..." value={content} onChange={(event) => setContent(event.target.value)} />
              </div>
              <DialogFooter><Button variant="outline" onClick={() => setOpen(false)}>Hủy</Button><Button onClick={() => void onImport()} disabled={isSaving}><Save className="h-4 w-4" />{isSaving ? "Đang nạp..." : "Nạp tài liệu"}</Button></DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
      <div className="rounded-lg border bg-white p-4">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input className="pl-9" placeholder="Tìm kiếm tài liệu..." />
        </div>
      </div>
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader><TableRow><TableHead>Tên tài liệu</TableHead><TableHead>Loại</TableHead><TableHead>Nguồn</TableHead><TableHead>Chunk</TableHead><TableHead>Trạng thái</TableHead><TableHead>Người tải</TableHead><TableHead>Hành động</TableHead></TableRow></TableHeader>
          <TableBody>
            {documents.map((doc) => (
              <TableRow key={doc.id || doc.name}>
                <TableCell className="font-medium"><span className="flex items-center gap-2"><FileText className="h-4 w-4 text-primary" />{doc.name}</span></TableCell>
                <TableCell>{doc.type}</TableCell>
                <TableCell>{doc.source}</TableCell>
                <TableCell>{doc.chunk_count || Math.ceil((doc.char_count || 0) / 500)} chunks</TableCell>
                <TableCell><StatusBadge tone={statusTone(doc.status)}>{doc.status}</StatusBadge></TableCell>
                <TableCell>{doc.owner}</TableCell>
                <TableCell><div className="flex gap-1"><Button variant="ghost" size="icon"><Eye className="h-4 w-4" /></Button><Button variant="ghost" size="icon"><RefreshCw className="h-4 w-4" /></Button><Button variant="ghost" size="icon"><Trash2 className="h-4 w-4 text-red-600" /></Button></div></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
