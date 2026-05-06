/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  logging: {
    fetches: { fullUrl: true },
  },
};

export default nextConfig;
