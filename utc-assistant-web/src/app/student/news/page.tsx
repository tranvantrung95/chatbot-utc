"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Newspaper } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiNews } from "@/lib/api-client";

export default function StudentNewsPage() {
  const [items, setItems] = useState<Array<{ id: string; title: string; summary: string; date: string; category: string; url: string }>>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiNews().then((response) => setItems(response.items)).catch((loadError) => setError(loadError instanceof Error ? loadError.message : "Không tải được tin tức."));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm font-medium text-primary">Cổng sinh viên</p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-950">Tin tức hoạt động</h1>
      </div>
      {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <Card key={item.id}>
            <CardHeader>
              <CardTitle className="flex items-start gap-2 text-base">
                <Newspaper className="mt-1 h-4 w-4 shrink-0 text-primary" />
                {item.title}
              </CardTitle>
              <CardDescription>{item.category} · {item.date}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-6 text-slate-600">{item.summary}</p>
              <a className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline" href={item.url} target="_blank">
                Xem chi tiết <ExternalLink className="h-4 w-4" />
              </a>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
