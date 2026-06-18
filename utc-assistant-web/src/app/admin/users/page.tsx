"use client";

import { useCallback, useEffect, useState } from "react";
import { Eye, KeyRound, Lock, Search, Unlock } from "lucide-react";
import { useAuth } from "@/components/shared/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { apiResetPassword, apiToggleLock, apiUsers, type ApiUser } from "@/lib/api-client";
import { StatusBadge, statusTone } from "@/components/shared/status-badge";

export default function AdminUsersPage() {
  const { token } = useAuth();
  const [users, setUsers] = useState<ApiUser[]>([]);
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const loadUsers = useCallback(async () => {
    if (!token) return;
    try {
      const response = await apiUsers(token, { q: query, role: roleFilter, status_filter: statusFilter });
      setUsers(response.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Không tải được người dùng.");
    }
  }, [query, roleFilter, statusFilter, token]);

  useEffect(() => { void loadUsers(); }, [loadUsers]);

  return (
    <div className="space-y-5">
      <div><p className="text-sm font-medium text-primary">Phân quyền SSO</p><h1 className="mt-1 text-2xl font-semibold">Quản lý người dùng</h1></div>
      {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
      {notice ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{notice}</div> : null}
      <div className="grid gap-3 rounded-lg border bg-white p-4 md:grid-cols-[1fr_180px_180px]">
        <div className="relative"><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><Input className="pl-9" placeholder="Tìm người dùng..." value={query} onChange={(event) => setQuery(event.target.value)} /></div>
        <Select value={roleFilter} onValueChange={setRoleFilter}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">Tất cả vai trò</SelectItem><SelectItem value="student">Sinh viên</SelectItem><SelectItem value="admin">Quản trị</SelectItem></SelectContent></Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">Tất cả trạng thái</SelectItem><SelectItem value="Đang hoạt động">Đang hoạt động</SelectItem><SelectItem value="Tạm khóa">Tạm khóa</SelectItem></SelectContent></Select>
      </div>
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader><TableRow><TableHead>Họ tên</TableHead><TableHead>Mã</TableHead><TableHead>Email</TableHead><TableHead>Vai trò</TableHead><TableHead>Đơn vị</TableHead><TableHead>Trạng thái</TableHead><TableHead>Hành động</TableHead></TableRow></TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="font-medium">{user.name}</TableCell>
                <TableCell>{user.identifier}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>{user.role_label}</TableCell>
                <TableCell>{user.faculty}</TableCell>
                <TableCell><StatusBadge tone={statusTone(user.status)}>{user.status}</StatusBadge></TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon"><Eye className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="icon" onClick={async () => { if (!token) return; await apiToggleLock(token, user.id); await loadUsers(); setNotice("Đã đổi trạng thái tài khoản."); }}>{user.status === "Tạm khóa" ? <Unlock className="h-4 w-4" /> : <Lock className="h-4 w-4" />}</Button>
                    <Button variant="ghost" size="icon" onClick={async () => { if (!token) return; const response = await apiResetPassword(token, user.id); setNotice(response.message); }}><KeyRound className="h-4 w-4" /></Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
