import { TranscriptSegment } from "@/lib/types";

export function findActiveSegmentIndex(segments: TranscriptSegment[], seconds: number): number {
  if (!segments.length) return -1;
  const exact = segments.findIndex(
    (segment) => seconds >= segment.startInSeconds && seconds < segment.endInSeconds,
  );
  if (exact >= 0) return exact;
  for (let index = segments.length - 1; index >= 0; index -= 1) {
    if (segments[index].startInSeconds <= seconds) return index;
  }
  return 0;
}

export function transcriptMatchIndexes(segments: TranscriptSegment[], query: string): number[] {
  const normalized = query.trim().toLocaleLowerCase();
  if (!normalized) return [];
  return segments.flatMap((segment, index) =>
    segment.text.toLocaleLowerCase().includes(normalized) ? [index] : [],
  );
}

export function splitHighlight(text: string, query: string): { value: string; match: boolean }[] {
  const normalized = query.trim();
  if (!normalized) return [{ value: text, match: false }];
  const parts: { value: string; match: boolean }[] = [];
  const lowerText = text.toLocaleLowerCase();
  const lowerQuery = normalized.toLocaleLowerCase();
  let cursor = 0;
  let matchAt = lowerText.indexOf(lowerQuery);
  while (matchAt >= 0) {
    if (matchAt > cursor) parts.push({ value: text.slice(cursor, matchAt), match: false });
    parts.push({ value: text.slice(matchAt, matchAt + normalized.length), match: true });
    cursor = matchAt + normalized.length;
    matchAt = lowerText.indexOf(lowerQuery, cursor);
  }
  if (cursor < text.length) parts.push({ value: text.slice(cursor), match: false });
  return parts.length ? parts : [{ value: text, match: false }];
}
