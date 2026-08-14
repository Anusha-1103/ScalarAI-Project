import type { AuthChangeEvent, Session } from "@supabase/supabase-js";

import {
  AccountProfile,
  ActionItem,
  ActionItemInput,
  AskAnswer,
  ApiResponse,
  DashboardData,
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

let accessToken: { value: string | null; expiresAt: number } | null = null;
let accessTokenRequest: Promise<string | null> | null = null;
let authListenerRegistered = false;

async function getAccessToken(): Promise<string | null> {
  const supabase = createClient();
  if (!supabase) return null;
  if (!authListenerRegistered) {
    supabase.auth.onAuthStateChange((_event: AuthChangeEvent, session: Session | null) => {
      accessToken = session
        ? { value: session.access_token, expiresAt: (session.expires_at ?? 0) * 1_000 }
        : { value: null, expiresAt: Number.POSITIVE_INFINITY };
    });
    authListenerRegistered = true;
  }
  if (accessToken && accessToken.expiresAt > Date.now() + 60_000) return accessToken.value;
  accessTokenRequest ??= supabase.auth.getSession().then(({ data }: { data: { session: Session | null } }) => {
    const session = data.session;
    accessToken = session
      ? { value: session.access_token, expiresAt: (session.expires_at ?? 0) * 1_000 }
      : { value: null, expiresAt: Number.POSITIVE_INFINITY };
    return accessToken.value;
  }).finally(() => {
    accessTokenRequest = null;
  });
  return accessTokenRequest;
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getAccessToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
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

export function getDashboard(): Promise<DashboardData> {
  return apiRequest("/dashboard?limit=50");
}

export function provisionSampleWorkspace(): Promise<DashboardData> {
  return apiRequest("/me/sample-workspace", { method: "POST" });
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
