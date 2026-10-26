"use client";

import { AlertTriangle, CheckCircle, Shield } from "lucide-react";

interface RiskCardProps {
  level: "low" | "medium" | "high";
  reason: string;
}

const riskStyles = {
  low: {
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    text: "text-emerald-800",
    iconBg: "bg-emerald-100",
    iconText: "text-emerald-600",
    label: "Low Risk",
    icon: CheckCircle,
  },
  medium: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    text: "text-amber-800",
    iconBg: "bg-amber-100",
    iconText: "text-amber-600",
    label: "Medium Risk",
    icon: AlertTriangle,
  },
  high: {
    bg: "bg-red-50",
    border: "border-red-200",
    text: "text-red-800",
    iconBg: "bg-red-100",
    iconText: "text-red-600",
    label: "High Risk",
    icon: Shield,
  },
};

export function RiskCard({ level, reason }: RiskCardProps) {
  const style = riskStyles[level];
  const Icon = style.icon;

  return (
    <div
      className={`${style.bg} ${style.border} border-l-4 rounded-r-lg p-4 mb-4 animate-fade-in`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <div
          className={`flex-shrink-0 p-2 rounded-lg ${style.iconBg} ${style.iconText}`}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`font-semibold ${style.text}`}>{style.label}</span>
          </div>
          <p className={`${style.text} leading-relaxed`}>{reason}</p>
        </div>
      </div>
    </div>
  );
}
