import {
  AccountProfile,
  ActionItem,
  ActionItemInput,
  AskAnswer,
  ApiResponse,
  MeetingDetail,
  MeetingMoment,
  MeetingUpdateInput,
  PaginatedMeetings,
  SearchResult,
  TranscriptSegment,
} from "@/lib/types";
import { createClient } from "@/lib/supabase/client";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const supabase = createClient();
  const session = supabase ? (await supabase.auth.getSession()).data.session : null;
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
      ...init?.headers,
    },
  });
  if (response.status === 204) return undefined as T;
  const payload = (await response.json()) as ApiResponse<T>;
  if (!response.ok || !payload.success) {
    throw new ApiRequestError(payload.error?.message ?? "The request could not be completed", response.status);
  }
  return payload.data;
}

export function getProfile(): Promise<AccountProfile> {
  return apiRequest("/me");
}

export function getMeetings(params: URLSearchParams): Promise<PaginatedMeetings> {
  return apiRequest(`/meetings?${params.toString()}`);
}

export function getMeeting(id: string): Promise<MeetingDetail> {
  return apiRequest(`/meetings/${id}`);
}

export function updateMeeting(id: string, payload: MeetingUpdateInput): Promise<MeetingDetail> {
  return apiRequest(`/meetings/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteMeeting(id: string): Promise<void> {
  return apiRequest(`/meetings/${id}`, { method: "DELETE" });
}

export function createActionItem(meetingId: string, payload: ActionItemInput): Promise<ActionItem> {
  return apiRequest(`/meetings/${meetingId}/action-items`, { method: "POST", body: JSON.stringify(payload) });
}

export function updateActionItem(id: string, payload: ActionItemInput): Promise<ActionItem> {
  return apiRequest(`/action-items/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteActionItem(id: string): Promise<void> {
  return apiRequest(`/action-items/${id}`, { method: "DELETE" });
}

export function globalSearch(query: string): Promise<SearchResult[]> {
  return apiRequest(`/search?q=${encodeURIComponent(query)}`);
}

export function askMeetingMemory(question: string): Promise<AskAnswer> {
  return apiRequest("/ask", { method: "POST", body: JSON.stringify({ question }) });
}

export function updateTranscriptSegment(id: string, text: string): Promise<TranscriptSegment> {
  return apiRequest(`/transcript-segments/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ text }),
  });
}

export function createMeetingMoment(
  meetingId: string,
  segmentId: string,
  kind: MeetingMoment["kind"] = "important",
): Promise<MeetingMoment> {
  return apiRequest(`/meetings/${meetingId}/moments`, {
    method: "POST",
    body: JSON.stringify({ segmentId, kind }),
  });
}

export function deleteMeetingMoment(id: string): Promise<void> {
  return apiRequest(`/moments/${id}`, { method: "DELETE" });
}
