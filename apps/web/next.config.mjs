/** @type {import('next').NextConfig} */
import { config } from '../../scripts/lib/env.mjs';
const settings = config();
const nextConfig = {
  distDir: process.env.NEXT_DIST_DIR || '.next',
  experimental: { proxyTimeout: 90000 },
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${settings.apiUrl}/api/:path*` }];
  },
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
