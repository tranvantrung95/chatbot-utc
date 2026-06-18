"use client";

import { useEffect, useState } from "react";
import {
  BookOpen, TrendingUp, AlertTriangle, CheckCircle2,
  GraduationCap, Lock, Star, Target,
} from "lucide-react";
import { apiRequest, apiStudentGrades, apiStudentProgress, apiStudentRecommendations } from "@/lib/api-client";

type GradesResponse = {
  gpa: number;
  courses: Course[];
};

type Course = {
  code: string;
  name: string;
  credits: number;
  qt: number;
  thi: number;
  total: number;
  grade: string;
  passed: boolean;
  semester: number;
};

type ProgressResponse = {
  gpa: number;
  earned: number;
  required: number;
  percent: number;
  warnings: string[];
};

type RecResponse = {
  available: Course[];
  locked: Course[];
};

function GradeBadge({ grade }: { grade: string }) {
  const colors: Record<string, string> = {
    A: "bg-emerald-100 text-emerald-700 border-emerald-200",
    B: "bg-sky-100 text-sky-700 border-sky-200",
    C: "bg-amber-100 text-amber-700 border-amber-200",
    D: "bg-orange-100 text-orange-700 border-orange-200",
    F: "bg-red-100 text-red-700 border-red-200",
  };
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold ${colors[grade] || "bg-slate-100 text-slate-600"}`}>
      {grade}
    </span>
  );
}

export default function StudentDashboardPage() {
  const [grades, setGrades] = useState<GradesResponse | null>(null);
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [recommendations, setRecommendations] = useState<RecResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };

    const opts = { method: "GET", headers };

    Promise.all([
      apiRequest<GradesResponse>("/api/student/grades", { token }),
      apiRequest<ProgressResponse>("/api/student/progress", { token }),
      apiRequest<RecResponse>("/api/student/recommendations", { token }),
    ])
      .then(([g, p, r]) => {
        setGrades(g);
        setProgress(p);
        setRecommendations(r);
      })
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Không tải được dữ liệu điểm.")
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary/20 border-t-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <p className="text-sm font-medium text-primary">Cổng sinh viên</p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-950">
          Học tập & Cá nhân
        </h1>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <GraduationCap className="h-4 w-4 text-primary" />
            GPA
          </div>
          <div className="mt-2 text-3xl font-bold text-slate-900">
            {progress?.gpa.toFixed(1)}
            <span className="text-base font-normal text-slate-400">/4.0</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <BookOpen className="h-4 w-4 text-sky-600" />
            Tín chỉ tích lũy
          </div>
          <div className="mt-2 text-3xl font-bold text-slate-900">
            {progress?.earned}
            <span className="text-base font-normal text-slate-400">
              /{progress?.required}
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Target className="h-4 w-4 text-emerald-600" />
            Tiến độ
          </div>
          <div className="mt-2 text-3xl font-bold text-slate-900">
            {progress?.percent}%
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <TrendingUp className="h-4 w-4 text-purple-600" />
            Môn đã qua
          </div>
          <div className="mt-2 text-3xl font-bold text-slate-900">
            {grades?.courses.filter((c) => c.passed).length}
            <span className="text-base font-normal text-slate-400">
              /{grades?.courses.length}
            </span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      {progress && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="text-slate-600">
              Tiến độ tốt nghiệp ({progress.earned}/{progress.required} tín chỉ)
            </span>
            <span className="font-semibold text-primary">{progress.percent}%</span>
          </div>
          <div className="h-3 w-full rounded-full bg-slate-100">
            <div
              className="h-3 rounded-full bg-gradient-to-r from-emerald-500 to-sky-500 transition-all duration-700"
              style={{ width: `${Math.min(progress.percent, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Warnings */}
      {progress && progress.warnings.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-center gap-2 font-semibold text-amber-800">
            <AlertTriangle className="h-4 w-4" />
            Cảnh báo
          </div>
          <ul className="mt-2 space-y-1">
            {progress.warnings.map((w, i) => (
              <li key={i} className="text-sm text-amber-700">{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Grades Table */}
      {grades && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-4 py-3">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
              <Star className="h-5 w-5 text-primary" />
              Bảng điểm
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
                  <th className="px-4 py-3">Mã môn</th>
                  <th className="px-4 py-3">Tên môn học</th>
                  <th className="px-4 py-3 text-center">TC</th>
                  <th className="px-4 py-3 text-center">QT</th>
                  <th className="px-4 py-3 text-center">Thi</th>
                  <th className="px-4 py-3 text-center">Tổng</th>
                  <th className="px-4 py-3 text-center">Điểm</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {grades.courses.map((c, i) => (
                  <tr
                    key={i}
                    className={
                      c.passed
                        ? "hover:bg-slate-50"
                        : "bg-red-50/50 hover:bg-red-50"
                    }
                  >
                    <td className="px-4 py-2.5 font-mono text-xs text-slate-500">
                      {c.code}
                    </td>
                    <td className="px-4 py-2.5 text-slate-800">{c.name}</td>
                    <td className="px-4 py-2.5 text-center text-slate-600">
                      {c.credits}
                    </td>
                    <td className="px-4 py-2.5 text-center text-slate-600">
                      {c.qt}
                    </td>
                    <td className="px-4 py-2.5 text-center text-slate-600">
                      {c.thi}
                    </td>
                    <td className="px-4 py-2.5 text-center font-medium text-slate-800">
                      {c.total}
                    </td>
                    <td className="px-4 py-2.5 text-center">
                      {c.passed ? (
                        <GradeBadge grade={c.grade} />
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-600">
                          <Lock className="h-3 w-3" />
                          {c.grade}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations && (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-emerald-200 bg-white shadow-sm">
            <div className="border-b border-emerald-100 px-4 py-3">
              <h2 className="flex items-center gap-2 text-lg font-semibold text-emerald-800">
                <CheckCircle2 className="h-5 w-5" />
                Có thể đăng ký
              </h2>
            </div>
            <div className="divide-y divide-slate-50 px-4 py-2">
              {recommendations.available.length === 0 ? (
                <p className="py-3 text-sm text-slate-500">
                  Không có môn mới khả dụng.
                </p>
              ) : (
                recommendations.available.map((c, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-2.5"
                  >
                    <div>
                      <p className="text-sm font-medium text-slate-800">
                        {c.name}
                      </p>
                      <p className="text-xs text-slate-400">
                        {c.code} · HK{c.semester}
                      </p>
                    </div>
                    <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                      {c.credits} TC
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-4 py-3">
              <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-600">
                <Lock className="h-5 w-5" />
                Chưa đủ điều kiện
              </h2>
            </div>
            <div className="divide-y divide-slate-50 px-4 py-2">
              {recommendations.locked.length === 0 ? (
                <p className="py-3 text-sm text-slate-500">
                  Tất cả môn đều khả dụng.
                </p>
              ) : (
                recommendations.locked.map((c, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-2.5"
                  >
                    <div>
                      <p className="text-sm text-slate-500">{c.name}</p>
                      <p className="text-xs text-slate-400">
                        {c.code} · HK{c.semester} · Cần môn tiên quyết
                      </p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">
                      {c.credits} TC
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
