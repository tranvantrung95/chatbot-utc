import type { LucideIcon } from "lucide-react";

export type UserRole = "student" | "admin";
export type StatusTone = "blue" | "green" | "red" | "amber" | "slate";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};
