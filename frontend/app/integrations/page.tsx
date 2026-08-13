import type { Metadata } from "next";

import { IntegrationsWorkspace } from "@/components/workspace-view";

export const metadata: Metadata = { title: "Integrations" };

export default function IntegrationsPage() { return <IntegrationsWorkspace />; }
