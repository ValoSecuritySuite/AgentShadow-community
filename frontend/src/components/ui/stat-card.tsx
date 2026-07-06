import * as React from "react";
import { cn } from "@/lib/utils";

export interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: React.ReactNode;
  value: React.ReactNode;
  subtitle?: React.ReactNode;
  icon?: React.ReactNode;
  accent?: "default" | "danger" | "warning" | "success";
}

const accentText: Record<string, string> = {
  default: "text-foreground",
  danger: "text-red-600 dark:text-red-400",
  warning: "text-amber-600 dark:text-amber-400",
  success: "text-emerald-600 dark:text-emerald-400",
};

export function StatCard({ className, label, value, subtitle, icon, accent = "default", ...props }: StatCardProps) {
  return (
    <div
      className={cn("rounded-xl border border-border bg-card p-5 shadow-sm transition-colors", className)}
      {...props}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="text-sm font-medium text-muted-foreground">{label}</div>
        {icon != null && (
          <span className="text-muted-foreground [&_svg]:size-4 [&_svg]:shrink-0">{icon}</span>
        )}
      </div>
      <div className={cn("mt-2 text-2xl font-semibold tracking-tight tabular-nums", accentText[accent])}>
        {value}
      </div>
      {subtitle != null && <div className="mt-1 text-xs text-muted-foreground">{subtitle}</div>}
    </div>
  );
}
