import type { Metadata } from "next";

import { CalendarWorkspace } from "@/components/workspace-view";

export const metadata: Metadata = { title: "Calendar" };

export default function CalendarPage() { return <CalendarWorkspace />; }
