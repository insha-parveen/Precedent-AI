import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL || "http://api:8000";

const nextConfig: NextConfig = {
  // Next 16 treats any origin other than `localhost` as cross-origin and blocks
  // its dev resources (HMR websocket, client chunks). React then never hydrates,
  // so the marketing page renders fully static — no GSAP, no scroll effects.
  // Users typically open 127.0.0.1:3000, so allow it explicitly in development.
  allowedDevOrigins: ["127.0.0.1", "localhost"],

  // Enable standalone output for Docker deployment
  output: "standalone",

  // Configure HTTP agent keep-alive for better connection reuse
  httpAgentOptions: {
    keepAlive: true,
  },

  // Increase server-side proxy timeout for long-running API requests (agent can take 15-60s)
  // This is needed because the Next.js rewrite proxy has a default timeout
  experimental: {
    proxyTimeout: 120000, // 2 minutes in milliseconds
  },

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
