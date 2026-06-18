"use client";

import { FormEvent, useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/components/shared/auth-provider";
import type { UserRole } from "@/lib/types";

export function AccountPage({ role }: { role: UserRole }) {
  const { user, changePassword } = useAuth();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const current = String(form.get("current") || "");
    const next = String(form.get("next") || "");
    const confirm = String(form.get("confirm") || "");
    if (!current || !next || !confirm) {
      setError("Vui lòng nhập đầy đủ các trường mật khẩu.");
      return;
    }
    if (next !== confirm) {
      setError("Mật khẩu xác nhận chưa khớp.");
      return;
    }
    try {
      const result = await changePassword(current, next);
      setMessage(result);
      setError("");
      event.currentTarget.reset();
    } catch (changeError) {
      setError(changeError instanceof Error ? changeError.message : "Không thể đổi mật khẩu lúc này.");
    }
  };

  if (!user) return null;

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm font-medium text-primary">Tài khoản</p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-950">Thông tin cá nhân</h1>
      </div>
      <div className="grid gap-5 lg:grid-cols-[1fr_420px]">
        <Card>
          <CardHeader>
            <CardTitle>Hồ sơ</CardTitle>
            <CardDescription>Thông tin tài khoản đang đăng nhập.</CardDescription>
          </CardHeader>
          <CardContent className="flex items-start gap-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback>{role === "admin" ? "QT" : "SV"}</AvatarFallback>
            </Avatar>
            <div className="grid gap-3 text-sm">
              <Info label="Họ tên" value={user.name} />
              <Info label="Mã sinh viên/email" value={user.identifier} />
              <Info label="Email" value={user.email} />
              <Info label="Đơn vị" value={user.faculty} />
              <Info label="Vai trò" value={user.role_label} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Đổi mật khẩu</CardTitle>
            <CardDescription>Cập nhật mật khẩu trực tiếp trên backend.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={onSubmit}>
              <PasswordInput id="current" label="Mật khẩu hiện tại" />
              <PasswordInput id="next" label="Mật khẩu mới" />
              <PasswordInput id="confirm" label="Xác nhận mật khẩu mới" />
              {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
              {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div> : null}
              <Button type="submit" className="w-full">Cập nhật mật khẩu</Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase text-slate-400">{label}</p>
      <p className="font-medium text-slate-800">{value}</p>
    </div>
  );
}

function PasswordInput({ id, label }: { id: string; label: string }) {
  return (
    <label className="block space-y-1.5 text-sm font-medium text-slate-700">
      <span>{label}</span>
      <Input id={id} name={id} type="password" placeholder="Nhập mật khẩu" />
    </label>
  );
}
