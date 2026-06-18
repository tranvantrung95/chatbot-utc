"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Eye, MessageSquareText, UserPlus } from "lucide-react";
import { useAuth } from "@/components/shared/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { apiBugs, apiFeedbackList } from "@/lib/api-client";
import { StatusBadge, statusTone } from "@/components/shared/status-badge";

export default function AdminFeedbackBugsPage() {
  const { token } = useAuth();
  const [feedbackRows, setFeedbackRows] = useState<Array<{ id: string; topic: string; student: string; satisfaction: string; content: string; status: string }>>([]);
  const [bugReports, setBugReports] = useState<Array<{ id: string; title: string; severity: string; status: string; assignee: string }>>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      if (!token) return;
      try {
        const [feedbackResponse, bugResponse] = await Promise.all([apiFeedbackList(token), apiBugs(token)]);
        setFeedbackRows(feedbackResponse.items);
        setBugReports(bugResponse.items);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Không tải được feedback/báo cáo lỗi.");
      }
    };
    void load();
  }, [token]);

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm font-medium text-primary">Quản trị</p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-950">Duyệt phản hồi</h1>
      </div>
      {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
      <Tabs defaultValue="feedback" className="space-y-4">
        <TabsList>
          <TabsTrigger value="feedback" className="gap-2"><MessageSquareText className="h-4 w-4" />Feedback</TabsTrigger>
          <TabsTrigger value="bugs" className="gap-2"><CheckCircle2 className="h-4 w-4" />Báo cáo lỗi</TabsTrigger>
        </TabsList>
        <TabsContent value="feedback">
          <Card>
            <CardHeader><CardTitle>Feedback sinh viên</CardTitle><CardDescription>Theo dõi mức độ hài lòng và trạng thái phản hồi.</CardDescription></CardHeader>
            <CardContent>
              <Table>
                <TableHeader><TableRow><TableHead>Chủ đề</TableHead><TableHead>Sinh viên</TableHead><TableHead>Mức độ</TableHead><TableHead>Nội dung</TableHead><TableHead>Trạng thái</TableHead><TableHead>Hành động</TableHead></TableRow></TableHeader>
                <TableBody>
                  {feedbackRows.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>{row.topic}</TableCell>
                      <TableCell>{row.student}</TableCell>
                      <TableCell><Badge variant="secondary">{row.satisfaction}</Badge></TableCell>
                      <TableCell>{row.content}</TableCell>
                      <TableCell><StatusBadge tone={statusTone(row.status)}>{row.status}</StatusBadge></TableCell>
                      <TableCell><Button variant="ghost" size="icon"><Eye className="h-4 w-4" /></Button></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="bugs">
          <Card>
            <CardHeader><CardTitle>Báo cáo lỗi</CardTitle><CardDescription>Theo dõi mức độ khẩn cấp và trạng thái xử lý.</CardDescription></CardHeader>
            <CardContent>
              <Table>
                <TableHeader><TableRow><TableHead>Lỗi</TableHead><TableHead>Mức độ</TableHead><TableHead>Trạng thái</TableHead><TableHead>Phụ trách</TableHead><TableHead>Hành động</TableHead></TableRow></TableHeader>
                <TableBody>
                  {bugReports.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>{row.title}</TableCell>
                      <TableCell><StatusBadge tone={statusTone(row.severity)}>{row.severity}</StatusBadge></TableCell>
                      <TableCell><StatusBadge tone={statusTone(row.status)}>{row.status}</StatusBadge></TableCell>
                      <TableCell>{row.assignee}</TableCell>
                      <TableCell><div className="flex gap-1"><Button variant="ghost" size="icon"><Eye className="h-4 w-4" /></Button><Button variant="ghost" size="icon"><UserPlus className="h-4 w-4" /></Button></div></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
