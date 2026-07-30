/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // i18n via next.config.js is not supported in the App Router.
  // Language detection/switching is handled in-app via the lang query param.

  // Allow <img> tags (not next/image) to load from the backend's /exports path
  // without being blocked by Next.js image optimisation restrictions.
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "branding-ai-backend.onrender.com",
        pathname: "/exports/**",
      },
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/exports/**",
      },
    ],
  },

};

module.exports = nextConfig;
