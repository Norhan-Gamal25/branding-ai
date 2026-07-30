// components/ui/badge.tsx
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default:  "bg-brand-100 text-brand-700 border border-brand-200",
        emerald:  "bg-emerald-100 text-emerald-700 border border-emerald-200",
        gold:     "bg-amber-100 text-amber-700 border border-amber-200",
        outline:  "border border-gray-200 text-gray-700 bg-white",
        approved: "bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
