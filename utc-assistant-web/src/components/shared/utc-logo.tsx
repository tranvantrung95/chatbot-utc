import Image from "next/image";

export function UtcLogo() {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-white ring-1 ring-slate-200">
        <Image src="/utc-emblem.png" alt="UTC" width={32} height={32} className="h-8 w-8 rounded-full object-contain" priority />
      </div>
      <div className="min-w-0">
        <p className="truncate text-sm font-extrabold text-[#0f294a]">UTC AI Assistant</p>
      </div>
    </div>
  );
}
