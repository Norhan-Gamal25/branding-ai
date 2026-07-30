// components/ui/button.tsx
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-lg text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:   "bg-brand-600 text-white hover:bg-brand-700 active:scale-95",
        secondary: "bg-white text-brand-700 border border-brand-200 hover:bg-brand-50 active:scale-95",
        ghost:     "hover:bg-brand-50 text-brand-700",
        destructive: "bg-red-600 text-white hover:bg-red-700",
        emerald:   "bg-emerald-600 text-white hover:bg-emerald-700 active:scale-95",
        outline:   "border border-brand-300 bg-transparent text-brand-700 hover:bg-brand-50",
      },
      size: {
        sm:   "h-8 px-3 text-xs",
        default: "h-10 px-5 py-2",
        lg:   "h-12 px-8 text-base",
        xl:   "h-14 px-10 text-lg",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
