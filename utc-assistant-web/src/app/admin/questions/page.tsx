"use client";

import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useAuth } from "@/components/shared/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { apiQuestions } from "@/lib/api-client";
import { StatusBadge, statusTone } from "@/components/shared/status-badge";

export default function AdminQuestionsPage() {
  const { token } = useAuth();
  const [questions, setQuestions] = useState<Array<{ id: string; question: string; topic: string; asker: string; time: string; status: string; rating: string }>>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    apiQuestions(token).then((response) => setQuestions(response.items)).catch((loadError) => setError(loadError instanceof Error ? loadError.message : "Không tải được câu hỏi."));
  }, [token]);

  const filtered = useMemo(() => questions.filter((item) => !query || item.question.toLowerCase().includes(query.toLowerCase())), [questions, query]);

  return (
    <div className="space-y-5">
      <div><p className="text-sm font-medium text-primary">Quản trị</p><h1 className="mt-1 text-2xl font-semibold">Giám sát câu hỏi</h1></div>
      <Card>
        <CardHeader><CardTitle>Bộ lọc câu hỏi</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="relative"><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><Input className="pl-9" placeholder="Tìm nội dung câu hỏi..." value={query} onChange={(event) => setQuery(event.target.value)} /></div>
          {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
          <Table>
            <TableHeader><TableRow><TableHead>Câu hỏi</TableHead><TableHead>Chủ đề</TableHead><TableHead>Người hỏi</TableHead><TableHead>Thời gian</TableHead><TableHead>Trạng thái</TableHead><TableHead>Đánh giá</TableHead></TableRow></TableHeader>
            <TableBody>
              {filtered.map((question) => (
                <TableRow key={question.id}>
                  <TableCell className="font-medium">{question.question}</TableCell>
                  <TableCell><Badge variant="secondary">{question.topic}</Badge></TableCell>
                  <TableCell>{question.asker}</TableCell>
                  <TableCell>{question.time}</TableCell>
                  <TableCell><StatusBadge tone={statusTone(question.status)}>{question.status}</StatusBadge></TableCell>
                  <TableCell>{question.rating}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
