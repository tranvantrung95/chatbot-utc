"use client";

import { FormEvent, useEffect, useState } from "react";
import { Bug } from "lucide-react";
import { useAuth } from "@/components/shared/auth-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { apiBugs, apiCreateBug } from "@/lib/api-client";
import { StatusBadge, statusTone } from "@/components/shared/status-badge";
import { EmptyState } from "@/components/shared/empty-state";

export default function StudentBugReportPage() {
  const { token } = useAuth();
  const [bugType, setBugType] = useState("Lỗi giao diện");
  const [severity, setSeverity] = useState("Trung bình");
  const [items, setItems] = useState<Array<{ id: string; title: string; severity: string; status: string }>>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    apiBugs(token).then((response) => setItems(response.items)).catch(() => undefined);
  }, [token]);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    try {
      const response = await apiCreateBug(token, {
        bug_type: bugType,
        severity,
        description: String(form.get("description") || ""),
        screenshot_note: "",
      });
      setMessage(response.message);
      setError("");
      event.currentTarget.reset();
      const bugResponse = await apiBugs(token);
      setItems(bugResponse.items);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Không gửi được báo cáo lỗi.");
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm font-medium text-primary">Cổng sinh viên</p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-950">Báo cáo lỗi</h1>
      </div>
      <div className="grid gap-5 lg:grid-cols-[1fr_420px]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bug className="h-5 w-5 text-primary" />
              Gửi báo cáo lỗi
            </CardTitle>
            <CardDescription>Mô tả lỗi bạn gặp trong quá trình sử dụng.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={onSubmit}>
              <Select value={bugType} onValueChange={setBugType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Lỗi giao diện">Lỗi giao diện</SelectItem>
                  <SelectItem value="Lỗi chatbot">Lỗi chatbot</SelectItem>
                  <SelectItem value="Lỗi đăng nhập">Lỗi đăng nhập</SelectItem>
                </SelectContent>
              </Select>
              <Select value={severity} onValueChange={setSeverity}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Thấp">Thấp</SelectItem>
                  <SelectItem value="Trung bình">Trung bình</SelectItem>
                  <SelectItem value="Cao">Cao</SelectItem>
                </SelectContent>
              </Select>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="bug-description">Mô tả lỗi</label>
                <Textarea id="bug-description" name="description" placeholder="Mô tả lỗi…" />
              </div>
              {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</div> : null}
              {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700" role="status">{message}</div> : null}
              <Button type="submit">Gửi báo cáo</Button>
            </form>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Báo cáo đã gửi</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {items.length === 0 ? (
              <EmptyState icon={Bug} title="Chưa có báo cáo lỗi" description="Các báo cáo lỗi bạn gửi sẽ hiển thị ở đây." />
            ) : (
              items.map((item) => (
                <div key={item.id} className="rounded-md border bg-slate-50 p-3 text-sm">
                  <p className="font-medium">{item.title}</p>
                  <div className="mt-2 flex gap-2">
                    <StatusBadge tone={statusTone(item.severity)}>{item.severity}</StatusBadge>
                    <StatusBadge tone={statusTone(item.status)}>{item.status}</StatusBadge>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
