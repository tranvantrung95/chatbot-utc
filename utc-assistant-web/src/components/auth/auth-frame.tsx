import Image from "next/image";
import Link from "next/link";

export function AuthFrame({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md rounded-lg border bg-white p-6 shadow-soft">
        <div className="mb-6 flex items-center gap-3">
          <Image
            src="/utc-emblem.png"
            alt="UTC Logo"
            width={44}
            height={44}
            className="h-11 w-11 rounded-lg object-contain"
            priority
          />
          <div>
            <h1 className="text-xl font-extrabold text-[#0f294a]">{title}</h1>
            <p className="text-sm text-slate-500">{subtitle}</p>
          </div>
        </div>
        {children}
        <div className="mt-5 flex justify-between text-sm">
          <Link className="font-medium text-primary hover:underline" href="/login">
            Đăng nhập
          </Link>
          <Link className="font-medium text-primary hover:underline" href="/register">
            Đăng ký
          </Link>
          <Link className="font-medium text-primary hover:underline" href="/forgot-password">
            Quên mật khẩu
          </Link>
        </div>
      </div>
    </main>
  );
}
