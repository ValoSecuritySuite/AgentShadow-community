import * as React from "react";
import { cn } from "@/lib/utils";

export interface SectionCardProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  padding?: "default" | "none";
}

export function SectionCard({
  className,
  title,
  description,
  action,
  children,
  padding = "default",
  ...props
}: SectionCardProps) {
  const hasHeader = title != null || description != null || action != null;
  return (
    <div className={cn("rounded-xl border border-border bg-card shadow-sm", className)} {...props}>
      {hasHeader && (
        <div className="flex flex-col gap-1 border-b border-border p-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            {title != null && <h3 className="text-base font-semibold tracking-tight">{title}</h3>}
            {description != null && <div className="mt-0.5 text-sm text-muted-foreground">{description}</div>}
          </div>
          {action != null && <div className="mt-2 shrink-0 sm:mt-0">{action}</div>}
        </div>
      )}
      {children != null && <div className={padding === "none" ? undefined : "p-5"}>{children}</div>}
    </div>
  );
}
