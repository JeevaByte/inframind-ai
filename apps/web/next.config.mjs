import path from "node:path"

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  outputFileTracingRoot: path.join(process.cwd(), "..", ".."),
  logging: {
    fetches: { fullUrl: true },
  },
}

export default nextConfig
