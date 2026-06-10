import { api } from "./client";
import type { CurrentBilling } from "./types";

export async function getCurrentBilling(): Promise<CurrentBilling> {
  const res = await api.get<CurrentBilling>("/billing/current");
  return res.data;
}
