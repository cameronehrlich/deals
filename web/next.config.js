/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://deals-api-swart.vercel.app/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
