"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthFrame } from "@/components/auth/auth-frame";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiRegister } from "@/lib/api-client";
import type { UserRole } from "@/lib/types";

export default function RegisterPage() {
  const router = useRouter();
  const [role, setRole] = useState<UserRole>("student");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const fullName = String(form.get("fullName") || "").trim();
    const identifier = String(form.get("studentId") || "").trim();
    const email = String(form.get("email") || "").trim();
    const password = String(form.get("password") || "");
    const confirmPassword = String(form.get("confirmPassword") || "");
    if (!fullName || !identifier || !email) {
      setError("Vui lòng nhập đầy đủ họ tên, mã định danh và email.");
      return;
    }
    if (password.length < 6) {
      setError("Mật khẩu tối thiểu 6 ký tự.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Mật khẩu xác nhận chưa khớp.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await apiRegister({ full_name: fullName, identifier, email, password, role });
      router.push("/login");
    } catch (registerError) {
      setError(registerError instanceof Error ? registerError.message : "Không thể đăng ký.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthFrame title="Đăng ký tài khoản" subtitle="Tạo tài khoản truy cập hệ thống trợ lý UTC.">
      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700" htmlFor="reg-fullName">Họ và tên</label>
          <Input id="reg-fullName" name="fullName" autoComplete="name" placeholder="Họ và tên" />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700" htmlFor="reg-studentId">Mã sinh viên hoặc email admin</label>
          <Input id="reg-studentId" name="studentId" autoComplete="username" placeholder="Mã sinh viên hoặc email admin" />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700" htmlFor="reg-email">Email</label>
          <Input id="reg-email" name="email" type="email" autoComplete="email" placeholder="Email" />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700" htmlFor="reg-password">Mật khẩu</label>
          <Input id="reg-password" name="password" type="password" autoComplete="new-password" placeholder="Mật khẩu tối thiểu 6 ký tự" />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700" htmlFor="reg-confirmPassword">Nhập lại mật khẩu</label>
          <Input id="reg-confirmPassword" name="confirmPassword" type="password" autoComplete="new-password" placeholder="Nhập lại mật khẩu" />
        </div>
        <Select value={role} onValueChange={(value: UserRole) => setRole(value)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="student">Sinh viên</SelectItem>
            <SelectItem value="admin">Quản trị viên</SelectItem>
          </SelectContent>
        </Select>
        {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</div> : null}
        <Button type="submit" className="w-full" disabled={loading}>{loading ? "Đang đăng ký…" : "Đăng ký"}</Button>
      </form>
    </AuthFrame>
  );
}
