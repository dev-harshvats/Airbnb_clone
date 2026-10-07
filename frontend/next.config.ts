import path from "node:path";
import type { NextConfig } from "next";

/**
 * The browser only ever talks to this origin. /api and /media are proxied to the
 * FastAPI backend, so the refresh-token cookie stays first-party (SYSTEM_DESIGN ADR-04).
 */
const API_ORIGIN = process.env.API_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    // Pin the project root so stray lockfiles in parent folders are never picked up.
    root: path.join(__dirname),
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${API_ORIGIN}/api/:path*` },
      { source: "/media/:path*", destination: `${API_ORIGIN}/media/:path*` },
    ];
  },
};

export default nextConfig;
