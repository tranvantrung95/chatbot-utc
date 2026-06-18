import { Badge } from "@/components/ui/badge";
import type { StatusTone } from "@/lib/types";
import { cn } from "@/lib/utils";

const toneClass: Record<StatusTone, string> = {
  blue: "border-blue-200 bg-blue-50 text-blue-700",
  green: "border-emerald-200 bg-emerald-50 text-emerald-700",
  red: "border-red-200 bg-red-50 text-red-700",
  amber: "border-amber-200 bg-amber-50 text-amber-700",
  slate: "border-slate-200 bg-slate-50 text-slate-700",
};

export function StatusBadge({
  children,
  tone = "slate",
  className,
}: {
  children: React.ReactNode;
  tone?: StatusTone;
  className?: string;
}) {
  return (
    <Badge variant="outline" className={cn("font-medium", toneClass[tone], className)}>
      {children}
    </Badge>
  );
}

export function statusTone(status: string): StatusTone {
  if (["Đã sẵn sàng", "Đã hoàn tất", "Hoàn tất", "Đã trả lời", "Đã phản hồi", "Đang hoạt động", "Thành công"].includes(status)) return "green";
  if (["Lỗi xử lý", "Tạm khóa", "Cao", "Thất bại"].includes(status)) return "red";
  if (["Đang xử lý", "Đang huấn luyện", "Cần kiểm tra", "Trung bình"].includes(status)) return "amber";
  if (["Đã tiếp nhận", "Chờ xử lý", "Chờ phản hồi"].includes(status)) return "blue";
  return "slate";
}
