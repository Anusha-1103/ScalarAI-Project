import type { Metadata } from "next";

import { MeetingsLibrary } from "@/components/meetings-library";

export const metadata: Metadata = { title: "Meetings" };

export default function MeetingsPage() {
  return <MeetingsLibrary />;
}
