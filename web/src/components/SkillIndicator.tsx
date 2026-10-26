"use client";

import { Badge } from "@/components/ui/Badge";

interface SkillIndicatorProps {
  skill: string | null | undefined;
  grounded: boolean | undefined;
}

export function SkillIndicator({ skill, grounded }: SkillIndicatorProps) {
  if (!skill) return null;

  return (
    <div className="flex items-center gap-2 mb-2">
      <Badge variant="secondary" className="text-xs">
        Skill: {skill}
      </Badge>
      {grounded === false && (
        <Badge variant="destructive" className="text-xs animate-pulse">
          âš  Not Grounded
        </Badge>
      )}
      {grounded === true && (
        <Badge variant="success" className="text-xs">
          âœ“ Grounded
        </Badge>
      )}
    </div>
  );
}
