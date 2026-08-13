import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { Providers } from "@/components/providers";

import "./globals.css";
import "./product-ui.css";

export const metadata: Metadata = {
  title: { default: "EchoNote", template: "%s · EchoNote" },
  description: "Searchable meeting notes, synchronized transcripts, and action items.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Providers><AppShell>{children}</AppShell></Providers>
      </body>
    </html>
  );
}
