"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import {
  Activity, BarChart3, CheckCircle2, Clock3, Database,
  FileQuestion, MessageSquareText, Users, TrendingUp,
  Zap, Circle, ArrowUpRight
} from "lucide-react";
import { useAuth } from "@/components/shared/auth-provider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { apiDashboard } from "@/lib/api-client";
import { StatusBadge, statusTone } from "@/components/shared/status-badge";
import { SkeletonCard } from "@/components/shared/skeleton";

function AnimatedNumber({ value, duration = 800 }: { value: string; duration?: number }) {
  const num = parseInt(value.replace(/[^0-9]/g, "")) || 0;
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    let start = 0;
    const step = Math.ceil(num / (duration / 16));
    const timer = setInterval(() => {
      start += step;
      if (start >= num) { setDisplay(num); clearInterval(timer); }
      else setDisplay(start);
    }, 16);
    return () => clearInterval(timer);
  }, [num, duration]);

  return <span ref={ref} className="tabular-nums">{display.toLocaleString()}{value.includes("%") ? "%" : ""}</span>;
}

const KPI_CARDS = [
  { key: "Tổng lượt truy cập", icon: Activity, color: "#6366f1", gradient: "from-indigo-500/20 to-indigo-600/5" },
  { key: "Số lượng câu hỏi", icon: FileQuestion, color: "#0ea5e9", gradient: "from-sky-500/20 to-sky-600/5" },
  { key: "Người dùng đang hoạt động", icon: Users, color: "#10b981", gradient: "from-emerald-500/20 to-emerald-600/5" },
  { key: "Tài liệu đã xử lý", icon: Database, color: "#f59e0b", gradient: "from-amber-500/20 to-amber-600/5" },
  { key: "Feedback mới", icon: MessageSquareText, color: "#ec4899", gradient: "from-pink-500/20 to-pink-600/5" },
];

export default function AdminDashboardPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState({
    kpis: [] as Array<{ label: string; value: string; delta: string }>,
    access_by_day: [] as Array<{ day: string; value: number }>,
    question_topics: [] as Array<{ label: string; value: number }>,
    success_rate: 0,
    avg_latency_sec: 0,
    recent_activities: [] as Array<{ id?: string; action: string; user: string; status: string; time: string }>,
  });

  useEffect(() => {
    const load = async () => {
      if (!token) return;
      try {
        setDashboard(await apiDashboard(token));
      } catch (e) { setError(e instanceof Error ? e.message : "Không tải được dashboard."); }
      finally { setLoading(false); }
    };
    void load();
  }, [token]);

  const maxAccess = Math.max(...dashboard.access_by_day.map(i => i.value), 1);
  const days = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      {/* Background pattern */}
      <div className="fixed inset-0 opacity-[0.015] pointer-events-none"
        style={{ backgroundImage: "radial-gradient(circle at 25% 25%, #0f294a 1px, transparent 1px), radial-gradient(circle at 75% 75%, #00828a 1px, transparent 1px)", backgroundSize: "60px 60px" }} />

      <div className="relative space-y-6 p-6 lg:p-8">
        {/* Header */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="h-1 w-8 rounded-full bg-gradient-to-r from-[#00828a] to-[#0f294a]" />
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#00828a]">Quản trị hệ thống</p>
            </div>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-[#0f294a]">Dashboard</h1>
            <p className="mt-1 text-sm text-slate-500">Tổng quan hoạt động trợ lý ảo UTC</p>
          </div>
          <div className="flex items-center gap-3 rounded-xl border bg-white/80 backdrop-blur px-4 py-2 text-sm text-slate-600 shadow-sm">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            Hệ thống đang hoạt động
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50/80 backdrop-blur px-4 py-3 text-sm text-red-700">{error}</div>
        )}

        {/* KPI Row */}
        <div className="flex gap-4 overflow-x-auto pb-1">
          {loading && dashboard.kpis.length === 0
            ? Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} />)
            : dashboard.kpis.map((item) => {
                const cfg = KPI_CARDS.find(c => c.key === item.label) || { icon: BarChart3, color: "#64748b", gradient: "from-slate-500/20" };
                const Icon = cfg.icon;
                return (
                  <div key={item.label}
                    className="group relative flex-1 min-w-0 overflow-hidden rounded-2xl border border-white/50 bg-white/70 backdrop-blur-xl p-5 shadow-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 hover:border-white/80">
                    <div className={`absolute inset-0 bg-gradient-to-br ${cfg.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                    <div className="relative">
                      <div className="flex items-start justify-between">
                        <div className="flex h-11 w-11 items-center justify-center rounded-xl shadow-sm transition-transform group-hover:scale-110 duration-300"
                          style={{ backgroundColor: `${cfg.color}15`, color: cfg.color }}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                          <ArrowUpRight className="h-3 w-3" />{item.delta}
                        </span>
                      </div>
                      <p className="mt-4 text-[28px] font-bold tracking-tight text-slate-900">
                        <AnimatedNumber value={item.value} />
                      </p>
                      <p className="mt-1 text-[13px] font-medium text-slate-500">{item.label}</p>
                    </div>
                  </div>
                );
              })
          }
        </div>

        {/* Charts Row */}
        <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
          {/* Access chart */}
          <div className="rounded-2xl border border-white/50 bg-white/70 backdrop-blur-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">Lượt truy cập</h3>
                <p className="text-sm text-slate-500">7 ngày gần nhất</p>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600">
                <Zap className="h-3.5 w-3.5 text-amber-500" />
                {dashboard.access_by_day.reduce((s, i) => s + i.value, 0)} lượt
              </div>
            </div>
            <div className="flex h-64 items-end gap-2">
              {dashboard.access_by_day.map((item, idx) => {
                const h = Math.max(4, Math.round((item.value / maxAccess) * 100));
                return (
                  <div key={item.day} className="group flex flex-1 flex-col items-center gap-2">
                    <span className="text-[11px] font-semibold text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity tabular-nums">{item.value}</span>
                    <div className="relative w-full flex-1">
                      <div className="absolute bottom-0 w-full rounded-t-lg transition-all duration-500 group-hover:brightness-110"
                        style={{
                          height: `${h}%`,
                          background: `linear-gradient(to top, ${idx % 2 === 0 ? '#00828a' : '#0f294a'}, ${idx % 2 === 0 ? '#0d9488' : '#1e40af'}40)`,
                        }} />
                    </div>
                    <span className="text-[11px] font-medium text-slate-500">{days[idx] || item.day}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Topics + Success */}
          <div className="space-y-6">
            <div className="rounded-2xl border border-white/50 bg-white/70 backdrop-blur-xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900 mb-5">Chủ đề câu hỏi</h3>
              <div className="space-y-4">
                {dashboard.question_topics.map((topic, idx) => (
                  <div key={topic.label} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-slate-700">{topic.label}</span>
                      <span className="tabular-nums text-slate-500">{topic.value}%</span>
                    </div>
                    <div className="relative h-2 overflow-hidden rounded-full bg-slate-100">
                      <div className="absolute inset-0 rounded-full transition-all duration-1000"
                        style={{
                          width: `${topic.value}%`,
                          background: `linear-gradient(to right, ${['#00828a','#0ea5e9','#6366f1','#f59e0b','#10b981','#ec4899'][idx % 6]}, ${['#0d9488','#0284c7','#4f46e5','#d97706','#059669','#db2777'][idx % 6]})`,
                        }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-white/50 bg-white/70 backdrop-blur-xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Hiệu suất</h3>
              <div className="flex items-center gap-5">
                <div className="relative flex h-24 w-24 items-center justify-center">
                  <svg className="absolute inset-0 -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="8" />
                    <circle cx="50" cy="50" r="42" fill="none" stroke="url(#grad)" strokeWidth="8"
                      strokeLinecap="round" strokeDasharray={`${dashboard.success_rate * 2.64} 264`} />
                    <defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#00828a"/><stop offset="100%" stopColor="#0f294a"/></linearGradient></defs>
                  </svg>
                  <span className="text-xl font-bold text-[#0f294a]">{Math.round(dashboard.success_rate)}%</span>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /><span className="text-slate-600">Phản hồi thành công <strong className="text-slate-900">{dashboard.success_rate}%</strong></span></div>
                  <div className="flex items-center gap-2"><Clock3 className="h-4 w-4 text-amber-500" /><span className="text-slate-600">Thời gian TB <strong className="text-slate-900">{dashboard.avg_latency_sec}s</strong></span></div>
                  <div className="flex items-center gap-2"><TrendingUp className="h-4 w-4 text-[#00828a]" /><span className="text-slate-600">Tỉ lệ hài lòng <strong className="text-slate-900">--</strong></span></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Activity */}
        <div className="rounded-2xl border border-white/50 bg-white/70 backdrop-blur-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900 mb-5">Hoạt động gần đây</h3>
          <div className="overflow-hidden rounded-xl border">
            <Table>
              <TableHeader className="bg-slate-50/80">
                <TableRow className="hover:bg-transparent">
                  <TableHead className="font-semibold text-slate-600">Hoạt động</TableHead>
                  <TableHead className="font-semibold text-slate-600">Người thực hiện</TableHead>
                  <TableHead className="font-semibold text-slate-600">Thời gian</TableHead>
                  <TableHead className="font-semibold text-slate-600 text-right">Trạng thái</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dashboard.recent_activities.map((a, idx) => (
                  <TableRow key={a.id || idx} className="group transition-colors hover:bg-slate-50/50">
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Circle className="h-2 w-2 fill-[#00828a] text-[#00828a]" />
                        {a.action}
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-600">{a.user}</TableCell>
                    <TableCell className="text-slate-500 tabular-nums">{a.time}</TableCell>
                    <TableCell className="text-right"><StatusBadge tone={statusTone(a.status)}>{a.status}</StatusBadge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  );
}
