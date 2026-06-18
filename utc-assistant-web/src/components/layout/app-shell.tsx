"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Bell,
  ChevronDown,
  LogOut,
  Menu,
  Shield,
  UserRound,
  X,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { adminNavItems, studentNavItems } from "@/lib/navigation";
import type { UserRole } from "@/lib/types";
import { cn } from "@/lib/utils";
import { roleLabel, useAuth } from "@/components/shared/auth-provider";

export function AppShell({ role, children }: { role: UserRole; children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, role: activeRole, isAuthenticated, isLoading, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const navItems = role === "admin" ? adminNavItems : studentNavItems;
  const isAdmin = role === "admin";

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated || !activeRole) {
      router.replace("/login");
      return;
    }
    if (activeRole !== role) {
      router.replace(activeRole === "admin" ? "/admin/dashboard" : "/student/chatbot");
    }
  }, [activeRole, isAuthenticated, isLoading, role, router]);

  useEffect(() => {
    if (!isAdmin) return;
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8001";
    fetch(`${backendUrl}/api/health`)
      .then((r) => r.ok && setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, [isAdmin]);

  const handleLogout = () => {
    void logout();
    router.push("/login");
  };

  const initials =
    user?.name
      ?.split(" ")
      .filter(Boolean)
      .slice(-2)
      .map((part) => part[0]?.toUpperCase() || "")
      .join("") || (isAdmin ? "QT" : "SV");

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm font-semibold text-slate-600">
        Đang tải thông tin tài khoản…
      </div>
    );
  }

  return (
    <div className="min-h-screen overflow-x-hidden bg-slate-50 text-slate-950">
      <a href="#main-content" className="skip-link">Bỏ qua điều hướng</a>
      <div
        className={cn("fixed inset-0 z-40 bg-slate-950/35 transition-opacity lg:hidden", open ? "opacity-100" : "pointer-events-none opacity-0")}
        onClick={() => setOpen(false)}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setOpen(false); }}
        role="button"
        tabIndex={0}
      />
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r shadow-soft transition-transform duration-200 lg:translate-x-0",
          isAdmin ? "rag-dark-panel border-slate-800 text-white" : "border-slate-200 bg-white text-slate-950",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className={cn("flex h-16 items-center justify-between border-b px-4", isAdmin ? "border-white/10" : "border-slate-200")}>
          <div className="flex min-w-0 items-center gap-3">
            <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg ring-1", isAdmin ? "bg-white ring-white/20" : "bg-white ring-slate-200")}>
              <Image src="/utc-emblem.png" alt="UTC" width={32} height={32} className="h-8 w-8 rounded-full object-contain" priority />
            </div>
            <div className="min-w-0">
              <p className={cn("truncate text-sm font-extrabold", isAdmin ? "text-white" : "text-[#0f294a]")}>UTC AI Assistant</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" className={cn("lg:hidden", isAdmin && "text-white hover:bg-white/10 hover:text-white")} onClick={() => setOpen(false)} aria-label="Đóng menu">
            <X className="h-5 w-5" />
          </Button>
        </div>

        <ScrollArea className="flex-1 px-3 py-4">
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-3 text-xs font-bold transition",
                    active && isAdmin && "bg-[#00828a] text-white shadow-line",
                    active && !isAdmin && "bg-[#0f294a] text-white shadow-line",
                    !active && isAdmin && "text-slate-300 hover:bg-white/10 hover:text-white",
                    !active && !isAdmin && "text-slate-600 hover:bg-slate-100 hover:text-[#0f294a]",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </ScrollArea>

        <div className={cn("mt-auto border-t p-3", isAdmin ? "border-white/10 bg-slate-950/25" : "border-slate-200 bg-slate-50")}>
          {isAdmin ? (
            <div className="mb-3 space-y-2 rounded-lg border border-white/10 bg-white/5 p-3 text-[11px] text-slate-300">
              <div className="flex justify-between gap-3">
                <span>Backend API</span>
                <span className={cn("font-bold", backendOnline === true ? "text-emerald-300" : backendOnline === false ? "text-red-300" : "text-amber-300")}>
                  {backendOnline === null ? "Đang kiểm tra…" : backendOnline ? "Online" : "Offline"}
                </span>
              </div>
              <div className="flex justify-between gap-3">
                <span>LLM Gateway</span>
                <span className={cn("font-bold", backendOnline === true ? "text-emerald-300" : "text-slate-500")}>
                  {backendOnline === true ? "Connected" : "—"}
                </span>
              </div>
            </div>
          ) : null}
          <Button variant="ghost" className={cn("w-full justify-start gap-3 text-red-600 hover:bg-red-50 hover:text-red-700", isAdmin && "text-red-200 hover:bg-red-500/10 hover:text-red-100")} onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            Đăng xuất
          </Button>
        </div>
      </aside>

      <div className="min-w-0 lg:pl-72">
        <header className="sticky top-0 z-30 flex h-16 min-w-0 items-center gap-3 border-b border-slate-200 bg-white/95 px-4 shadow-sm backdrop-blur md:px-6">
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(true)} aria-label="Mở menu">
            <Menu className="h-5 w-5" />
          </Button>

          <div className="ml-auto flex min-w-0 items-center gap-2">
            <Button variant="outline" size="icon" aria-label="Thông báo" className="rounded-lg">
              <Bell className="h-4 w-4" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="min-w-0 gap-2 rounded-lg px-2">
                  <Avatar className="h-9 w-9">
                    <AvatarFallback className="bg-gradient-to-br from-[#0f294a] to-[#00828a] text-xs font-bold text-white">{initials}</AvatarFallback>
                  </Avatar>
                  <span className="hidden max-w-40 truncate text-right md:inline">
                    <span className="block truncate text-sm font-bold text-[#0f294a]">{user.name}</span>
                    <span className="block truncate text-[11px] text-slate-500">{user.identifier || user.email}</span>
                  </span>
                  <ChevronDown className="h-4 w-4 text-slate-500" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-60">
                <DropdownMenuLabel>
                  <span className="block truncate">{user.name}</span>
                  <span className="block truncate text-xs font-normal text-slate-500">{user.email}</span>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => router.push(`/${role}/account`)}>
                  {isAdmin ? <Shield className="mr-2 h-4 w-4" /> : <UserRound className="mr-2 h-4 w-4" />}
                  Tài khoản
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  Đăng xuất
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>
        <main id="main-content" className="mx-auto w-full max-w-[1480px] min-w-0 overflow-x-hidden px-4 py-5 md:px-6 md:py-6">{children}</main>
      </div>
    </div>
  );
}
