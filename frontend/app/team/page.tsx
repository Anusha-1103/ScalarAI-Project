import type { Metadata } from "next";

import { TeamWorkspace } from "@/components/workspace-view";

export const metadata: Metadata = { title: "People" };

export default function TeamPage() { return <TeamWorkspace />; }
