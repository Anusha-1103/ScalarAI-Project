import type { Metadata } from "next";

import { SettingsWorkspace } from "@/components/workspace-view";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() { return <SettingsWorkspace />; }
