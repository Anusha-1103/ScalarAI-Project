import { describe, expect, it } from "vitest";

import { findActiveSegmentIndex, splitHighlight, transcriptMatchIndexes } from "./transcript";
import { TranscriptSegment } from "./types";

const segments = [
  { id: "one", sequenceNumber: 0, startInSeconds: 0, endInSeconds: 8, text: "Welcome team", speaker: null },
  { id: "two", sequenceNumber: 1, startInSeconds: 10, endInSeconds: 20, text: "Review the launch plan", speaker: null },
] satisfies TranscriptSegment[];

describe("transcript helpers", () => {
  it("finds the current segment and carries the previous segment through gaps", () => {
    expect(findActiveSegmentIndex(segments, 4)).toBe(0);
    expect(findActiveSegmentIndex(segments, 9)).toBe(0);
    expect(findActiveSegmentIndex(segments, 12)).toBe(1);
  });

  it("returns case-insensitive transcript matches", () => {
    expect(transcriptMatchIndexes(segments, "LAUNCH")).toEqual([1]);
    expect(transcriptMatchIndexes(segments, "  ")).toEqual([]);
  });

  it("splits every matching phrase without losing original casing", () => {
    expect(splitHighlight("Plan the plan", "plan")).toEqual([
      { value: "Plan", match: true },
      { value: " the ", match: false },
      { value: "plan", match: true },
    ]);
  });
});
