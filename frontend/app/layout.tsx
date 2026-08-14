import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";

import { AppShell } from "@/components/app-shell";
import { Providers } from "@/components/providers";

import "./globals.css";
import "./product-ui.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://scalarai-project.vercel.app"),
  title: { default: "EchoNote", template: "%s · EchoNote" },
  description: "Searchable meeting notes, synchronized transcripts, and action items.",
  icons: {
    icon: "/brand/favicon.svg",
    shortcut: "/brand/favicon.svg",
    apple: "/brand/echonote-app-icon.svg",
  },
  openGraph: {
    title: "EchoNote",
    description: "AI meeting memory for searchable conversations, grounded answers, and follow-through.",
    type: "website",
    images: [{ url: "/og/echonote-github-social.png", width: 1280, height: 640, alt: "EchoNote AI meeting memory" }],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `(function(){try{var saved=localStorage.getItem("echonote-theme");var theme=saved||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");document.documentElement.dataset.theme=theme;}catch(_){document.documentElement.dataset.theme="light";}})();` }} />
      </head>
      <body>
        <Providers><AppShell>{children}</AppShell></Providers>
        <Analytics />
      </body>
    </html>
  );
}
