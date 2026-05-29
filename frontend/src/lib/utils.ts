import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Tailwind class concatenation helper used across shadcn components. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
