import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { getUpgradeUrl, type LockedFeature } from "@/lib/edition";
import { ProBadge } from "@/components/ui/pro-badge";

/** A compact inline "locked" callout for a specific premium feature. */
export function LockedFeatureCallout({
  feature,
  className,
}: {
  feature: LockedFeature;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-lg border border-dashed border-border bg-muted/40 p-4",
        className,
      )}
    >
      <div className="flex items-center gap-2">
        <ProBadge tier={feature.tier} />
        <span className="text-sm font-semibold">{feature.title}</span>
      </div>
      <p className="text-sm text-muted-foreground">{feature.description}</p>
      <UpgradeButton size="sm" label={`Unlock with ${feature.tier}`} />
    </div>
  );
}

/** Standalone upgrade button that links to the pricing/upgrade page. */
export function UpgradeButton({
  label = "Upgrade to Pro",
  size = "default",
  className,
}: {
  label?: string;
  size?: "default" | "sm";
  className?: string;
}) {
  return (
    <Link
      href={getUpgradeUrl()}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md bg-violet-600 font-medium text-white transition-colors hover:bg-violet-700",
        size === "sm" ? "h-8 px-3 text-xs" : "h-9 px-4 text-sm",
        className,
      )}
    >
      <Sparkles className={size === "sm" ? "size-3.5" : "size-4"} />
      {label}
      <ArrowRight className={size === "sm" ? "size-3.5" : "size-4"} />
    </Link>
  );
}
