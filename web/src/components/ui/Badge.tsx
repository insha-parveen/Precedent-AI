"use client";

import { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  variant?: "default" | "secondary" | "destructive" | "success" | "outline";
  className?: string;
}

const variants = {
  default: "bg-ink text-white",
  secondary: "bg-sand text-ink border border-sand-deep",
  destructive: "bg-red-100 text-red-700 border border-red-200",
  success: "bg-emerald-100 text-emerald-700 border border-emerald-200",
  outline: "bg-transparent border border-sand-deep text-ink",
};

export function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}