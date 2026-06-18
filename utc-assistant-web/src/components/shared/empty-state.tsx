import { cn } from "@/lib/utils";
import { type LucideIcon, PackageOpen } from "lucide-react";

type EmptyStateProps = {
  icon?: LucideIcon;
  title?: string;
  description?: string;
  className?: string;
};

export function EmptyState({
  icon: Icon = PackageOpen,
  title = "Chưa có dữ liệu",
  description,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 text-center", className)}>
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
        <Icon className="h-6 w-6 text-slate-400" />
      </div>
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      {description ? <p className="mt-1 max-w-xs text-xs text-slate-500">{description}</p> : null}
    </div>
  );
}
