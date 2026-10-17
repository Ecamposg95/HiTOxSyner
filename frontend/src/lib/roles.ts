import type { User } from "../types";

export type Capability = "write" | "approveDecision" | "comment" | "manageLab" | "viewLabSummary";

export function can(user: User | null, capability: Capability): boolean {
  if (!user) return false;
  switch (capability) {
    case "write":
    case "manageLab":
      return user.role === "SYNER_ADMIN";
    case "approveDecision":
    case "viewLabSummary":
      return user.role === "SYNER_ADMIN" || user.role === "HITO_EXECUTIVE";
    case "comment":
      return true;
  }
}
