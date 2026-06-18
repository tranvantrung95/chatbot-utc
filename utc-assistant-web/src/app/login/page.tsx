"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthFrame } from "@/components/auth/auth-frame";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/components/shared/auth-provider";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!identifier.trim()) {
      setError("Vui lòng nhập mã sinh viên hoặc email.");
      return;
    }
    if (password.length < 6) {
      setError("Mật khẩu tối thiểu 6 ký tự.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const user = await login(identifier.trim(), password);
      router.push(user.role === "admin" ? "/admin/dashboard" : "/student/chatbot");
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Không đăng nhập được.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthFrame title="Đăng nhập UTC AI" subtitle="Dùng tài khoản sinh viên hoặc cán bộ quản trị.">
      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700" htmlFor="identifier">
            Mã sinh viên hoặc email
          </label>
          <Input id="identifier" name="identifier" autoComplete="username" placeholder="K66CNTT001 hoặc admin@utc.edu.vn" value={identifier} onChange={(event) => setIdentifier(event.target.value)} />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700" htmlFor="password">
            Mật khẩu
          </label>
          <Input id="password" name="password" type="password" autoComplete="current-password" placeholder="Nhập mật khẩu" value={password} onChange={(event) => setPassword(event.target.value)} />
        </div>
        {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</div> : null}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Đang đăng nhập…" : "Đăng nhập"}
        </Button>
      </form>
      <p className="mt-4 text-xs leading-5 text-slate-500">
        Tài khoản mặc định backend: <code>K66CNTT001</code> hoặc <code>admin@utc.edu.vn</code>, mật khẩu <code>12345678</code>.
        <br />
        <Link className="font-medium text-primary hover:underline" href="/forgot-password">Quên mật khẩu?</Link>
      </p>
    </AuthFrame>
  );
}
