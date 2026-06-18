"use client";

import { FormEvent, useState } from "react";
import { AuthFrame } from "@/components/auth/auth-frame";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiForgotPassword } from "@/lib/api-client";

export default function ForgotPasswordPage() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") || "").trim();
    if (!email) {
      setError("Vui lòng nhập email.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await apiForgotPassword(email);
      setMessage(response.message);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Không gửi được yêu cầu.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthFrame title="Quên mật khẩu" subtitle="Nhập email đã đăng ký để nhận hướng dẫn đặt lại mật khẩu.">
      <form className="space-y-4" onSubmit={onSubmit}>
        <Input name="email" type="email" placeholder="Email đã đăng ký" />
        {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
        {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div> : null}
        <Button type="submit" className="w-full" disabled={loading}>{loading ? "Đang gửi..." : "Gửi yêu cầu"}</Button>
      </form>
    </AuthFrame>
  );
}
