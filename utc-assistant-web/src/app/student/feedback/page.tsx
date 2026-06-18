"use client";

import { FormEvent, useState } from "react";
import { MessageSquareText } from "lucide-react";
import { useAuth } from "@/components/shared/auth-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { apiCreateFeedback } from "@/lib/api-client";

export default function StudentFeedbackPage() {
  const { token, user } = useAuth();
  const [satisfaction, setSatisfaction] = useState("Hài lòng");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    try {
      const response = await apiCreateFeedback(token, {
        subject: String(form.get("subject") || "Góp ý chatbot"),
        satisfaction,
        content: String(form.get("content") || ""),
        email: String(form.get("email") || user?.email || ""),
      });
      setMessage(response.message);
      setError("");
      event.currentTarget.reset();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Không gửi được feedback.");
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm font-medium text-primary">Cổng sinh viên</p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-950">Feedback</h1>
      </div>
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquareText className="h-5 w-5 text-primary" />
            Gửi góp ý
          </CardTitle>
          <CardDescription>Phản hồi chất lượng câu trả lời hoặc trải nghiệm sử dụng.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700" htmlFor="fb-subject">Chủ đề góp ý</label>
              <Input id="fb-subject" name="subject" placeholder="Chủ đề góp ý…" />
            </div>
            <Select value={satisfaction} onValueChange={setSatisfaction}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Rất hài lòng">Rất hài lòng</SelectItem>
                <SelectItem value="Hài lòng">Hài lòng</SelectItem>
                <SelectItem value="Chưa hài lòng">Chưa hài lòng</SelectItem>
              </SelectContent>
            </Select>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700" htmlFor="fb-content">Nội dung góp ý</label>
              <Textarea id="fb-content" name="content" placeholder="Nội dung góp ý…" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700" htmlFor="fb-email">Email liên hệ</label>
              <Input id="fb-email" name="email" type="email" defaultValue={user?.email || ""} placeholder="Email liên hệ" />
            </div>
            {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</div> : null}
            {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700" role="status">{message}</div> : null}
            <Button type="submit">Gửi feedback</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
