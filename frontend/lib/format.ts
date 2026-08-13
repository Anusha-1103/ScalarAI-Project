import { format, formatDistanceToNowStrict, isToday, isYesterday } from "date-fns";

export function formatDuration(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  if (hours) return `${hours}h ${minutes}m`;
  return `${Math.max(minutes, 1)} min`;
}

export function formatTimestamp(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remaining = Math.floor(seconds % 60);
  return `${minutes}:${remaining.toString().padStart(2, "0")}`;
}

export function formatMeetingDate(value: string): string {
  const date = new Date(value);
  if (isToday(date)) return `Today, ${format(date, "h:mm a")}`;
  if (isYesterday(date)) return `Yesterday, ${format(date, "h:mm a")}`;
  return format(date, "MMM d, yyyy · h:mm a");
}

export function formatRelativeDate(value: string): string {
  return formatDistanceToNowStrict(new Date(value), { addSuffix: true });
}
