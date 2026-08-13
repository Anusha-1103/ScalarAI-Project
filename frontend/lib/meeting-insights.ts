import { TranscriptSegment } from "@/lib/types";

export type SmartFilter = "all" | "questions" | "tasks" | "metrics";

const stopWords = new Set([
  "about", "after", "again", "also", "and", "before", "but", "can", "for", "from",
  "have", "into", "just", "need", "our", "that", "the", "their", "then", "this", "today",
  "will", "with", "would", "you", "your",
]);

export function matchesSmartFilter(segment: TranscriptSegment, filter: SmartFilter): boolean {
  const text = segment.text.toLocaleLowerCase();
  if (filter === "questions") return text.includes("?") || /\b(what|why|how|when|where|who|can we|should we)\b/.test(text);
  if (filter === "tasks") return /\b(i will|we will|need to|follow up|action item|by (monday|tuesday|wednesday|thursday|friday|tomorrow))\b/.test(text);
  if (filter === "metrics") return /\d|%|\b(percent|rate|revenue|users|minutes|hours)\b/.test(text);
  return true;
}

export function buildMeetingInsights(segments: TranscriptSegment[]) {
  const speakerSeconds = new Map<string, number>();
  const words = new Map<string, number>();
  let positive = 0;
  let concern = 0;
  for (const segment of segments) {
    const speaker = segment.speaker?.name ?? "Unknown";
    speakerSeconds.set(speaker, (speakerSeconds.get(speaker) ?? 0) + segment.endInSeconds - segment.startInSeconds);
    const text = segment.text.toLocaleLowerCase();
    if (/\b(great|good|agreed|perfect|strong|improved|works)\b/.test(text)) positive += 1;
    if (/\b(concern|risk|issue|blocker|missed|error|uncertain|gap)\b/.test(text)) concern += 1;
    text.match(/[a-z]{4,}/g)?.forEach((word) => {
      if (!stopWords.has(word)) words.set(word, (words.get(word) ?? 0) + 1);
    });
  }
  const totalSeconds = [...speakerSeconds.values()].reduce((sum, value) => sum + value, 0) || 1;
  return {
    speakers: [...speakerSeconds.entries()].map(([name, seconds]) => ({ name, seconds, percent: Math.round((seconds / totalSeconds) * 100) })).sort((a, b) => b.seconds - a.seconds),
    topics: [...words.entries()].sort((a, b) => b[1] - a[1]).slice(0, 7).map(([word, count]) => ({ word, count })),
    questions: segments.filter((segment) => matchesSmartFilter(segment, "questions")).length,
    tasks: segments.filter((segment) => matchesSmartFilter(segment, "tasks")).length,
    metrics: segments.filter((segment) => matchesSmartFilter(segment, "metrics")).length,
    sentiment: positive > concern ? "Positive" : concern > positive ? "Concerned" : "Balanced",
  };
}
