import type { Metadata } from "next";

import { AskEcho } from "@/components/ask-echo";

export const metadata: Metadata = { title: "Ask Echo" };

export default function AskPage() {
  return <AskEcho />;
}
