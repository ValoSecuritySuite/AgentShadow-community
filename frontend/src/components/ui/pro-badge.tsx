import { Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Tier } from "@/lib/edition";

const tierClasses: Record<Tier, string> = {
  Pro: "border-violet-200 bg-violet-50 text-violet-700 dark:border-violet-900/50 dark:bg-violet-950/50 dark:text-violet-300",
  Enterprise:
    "border-indigo-200 bg-indigo-50 text-indigo-700 dark:border-indigo-900/50 dark:bg-indigo-950/50 dark:text-indigo-300",
};

export function ProBadge({ tier = "Pro", className }: { tier?: Tier; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
        tierClasses[tier],
        className,
      )}
    >
      <Lock className="size-3" strokeWidth={2.5} />
      {tier}
    </span>
  );
}
