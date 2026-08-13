import { describe, expect, it } from "vitest";

import { buildMeetingInsights, matchesSmartFilter } from "./meeting-insights";
import { TranscriptSegment } from "./types";

const segments = [
  { id: "1", sequenceNumber: 0, startInSeconds: 0, endInSeconds: 10, text: "Can we improve activation by 20 percent?", speaker: { id: "a", name: "Anusha", email: null, avatarColor: "#000", isHost: true } },
  { id: "2", sequenceNumber: 1, startInSeconds: 10, endInSeconds: 30, text: "Great. I will share the activation report by Friday.", speaker: { id: "b", name: "Maya", email: null, avatarColor: "#111", isHost: false } },
] satisfies TranscriptSegment[];

describe("meeting intelligence", () => {
  it("classifies smart-search segments", () => {
    expect(matchesSmartFilter(segments[0], "questions")).toBe(true);
    expect(matchesSmartFilter(segments[1], "tasks")).toBe(true);
    expect(matchesSmartFilter(segments[0], "metrics")).toBe(true);
  });

  it("calculates talk time and recurring topics", () => {
    const insights = buildMeetingInsights(segments);
    expect(insights.speakers[0]).toMatchObject({ name: "Maya", percent: 67 });
    expect(insights.topics[0]).toMatchObject({ word: "activation", count: 2 });
    expect(insights.sentiment).toBe("Positive");
  });
});
