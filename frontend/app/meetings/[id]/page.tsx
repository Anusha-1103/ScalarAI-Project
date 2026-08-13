import type { Metadata } from "next";

import { MeetingWorkspace } from "@/components/meeting-workspace";

export const metadata: Metadata = { title: "Meeting" };

export default async function MeetingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <MeetingWorkspace meetingId={id} />;
}
