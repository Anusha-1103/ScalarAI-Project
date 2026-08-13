export interface Participant {
  id: string;
  name: string;
  email: string | null;
  avatarColor: string;
  isHost: boolean;
}

export interface MeetingListItem {
  id: string;
  title: string;
  meetingAtUtc: string;
  durationInSeconds: number;
  sourceType: string;
  participants: Participant[];
  summaryPreview: string | null;
  actionItemCount: number;
  completedActionItemCount: number;
}

export interface TranscriptSegment {
  id: string;
  sequenceNumber: number;
  startInSeconds: number;
  endInSeconds: number;
  text: string;
  speaker: Participant | null;
}

export interface ActionItem {
  id: string;
  description: string;
  isCompleted: boolean;
  dueAtUtc: string | null;
  assignee: Participant | null;
  createdAtUtc: string;
  updatedAtUtc: string;
}

export interface MeetingDetail extends MeetingListItem {
  mediaUrl: string | null;
  transcriptSegments: TranscriptSegment[];
  summary: { overview: string; keyPoints: string[] } | null;
  chapters: { id: string; title: string; startInSeconds: number }[];
  actionItems: ActionItem[];
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error: { code: string; message: string; details: Record<string, unknown> } | null;
}

export interface PaginatedMeetings {
  items: MeetingListItem[];
  pagination: { page: number; limit: number; totalItems: number; totalPages: number };
}

export interface MeetingUpdateInput {
  title?: string;
  meetingAtUtc?: string;
  participantNames?: string[];
}

export interface ActionItemInput {
  description?: string;
  assigneeParticipantId?: string | null;
  dueAtUtc?: string | null;
  isCompleted?: boolean;
}

export interface SearchResult {
  meetingId: string;
  meetingTitle: string;
  meetingAtUtc: string;
  segmentId: string | null;
  startInSeconds: number | null;
  snippet: string;
  resultType: string;
}
