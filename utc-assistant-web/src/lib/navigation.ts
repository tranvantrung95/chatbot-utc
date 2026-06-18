import {
  AlertCircle,
  BarChart3,
  Bot,
  Bug,
  Database,
  FileQuestion,
  Home,
  List,
  MessageSquareText,
  Newspaper,
  Settings,
  UploadCloud,
  User,
  Users,
} from "lucide-react";
import type { NavItem } from "@/lib/types";

export const studentNavItems: NavItem[] = [
  { label: "Học tập & Cá nhân", href: "/student/dashboard", icon: BarChart3 },
  { label: "Chat hỏi đáp", href: "/student/chatbot", icon: Bot },
  { label: "Tin tức hoạt động", href: "/student/news", icon: Newspaper },
  { label: "Feedback", href: "/student/feedback", icon: MessageSquareText },
  { label: "Báo cáo lỗi", href: "/student/bug-report", icon: Bug },
  { label: "Tài khoản", href: "/student/account", icon: User },
];

export const adminNavItems: NavItem[] = [
  { label: "Bảng thống kê", href: "/admin/dashboard", icon: Home },
  { label: "Tài liệu RAG", href: "/admin/documents", icon: Database },
  { label: "Nhập tài liệu", href: "/admin/import", icon: UploadCloud },
  { label: "Cấu hình RAG", href: "/admin/config", icon: Settings },
  { label: "Người dùng", href: "/admin/users", icon: Users },
  { label: "Giám sát câu hỏi", href: "/admin/questions", icon: FileQuestion },
  { label: "Duyệt phản hồi", href: "/admin/feedback-bugs", icon: AlertCircle },
  { label: "Nhật ký hệ thống", href: "/admin/logs", icon: List },
  { label: "Tài khoản", href: "/admin/account", icon: User },
];

export const suggestedQuestions = [
  "Học phí kỳ này",
  "Lịch thi",
  "Điểm rèn luyện",
  "Xin giấy xác nhận sinh viên",
  "Ký túc xá",
];
