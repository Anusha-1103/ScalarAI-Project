import type { NextConfig } from "next";

function origin(value: string | undefined): string | null {
  if (!value) return null;
  try {
    return new URL(value).origin;
  } catch {
    return null;
  }
}

const apiOrigin = origin(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1");
const supabaseOrigin = origin(process.env.NEXT_PUBLIC_SUPABASE_URL);
const connectSources = ["'self'", apiOrigin, supabaseOrigin, supabaseOrigin?.replace("https://", "wss://")]
  .filter(Boolean)
  .join(" ");
const imageSources = ["'self'", "data:", "blob:", supabaseOrigin].filter(Boolean).join(" ");
const contentSecurityPolicy = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  `img-src ${imageSources}`,
  "font-src 'self' data:",
  `connect-src ${connectSources}`,
  "media-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "upgrade-insecure-requests",
].join("; ");

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  experimental: {
    webpackBuildWorker: false,
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Content-Security-Policy", value: contentSecurityPolicy },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(), geolocation=(), microphone=()" },
          { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
        ],
      },
    ];
  },
};

export default nextConfig;
