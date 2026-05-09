import { PHASE_DEVELOPMENT_SERVER } from "next/constants.js";

const backendApiUrl = (process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

/** @type {import('next').NextConfig} */
const baseConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendApiUrl}/:path*`
      }
    ];
  }
};

export default function nextConfig(phase) {
  return {
    ...baseConfig,
    distDir: phase === PHASE_DEVELOPMENT_SERVER ? ".next-dev" : ".next"
  };
}
