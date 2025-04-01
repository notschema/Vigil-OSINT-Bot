/** @type {import('next').NextConfig} */
const nextConfig = {
  // Basic Next.js configuration
  reactStrictMode: true,
  swcMinify: true,
  
  // Ensure proper path configurations
  basePath: '',
  assetPrefix: '',

  // Configure public runtime config
  publicRuntimeConfig: {
    apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
  },

  // Server configuration
  experimental: {
    serverComponentsExternalPackages: [],
  },

  // Webpack configuration if needed
  webpack: (config) => {
    config.resolve.fallback = { fs: false, net: false, tls: false };
    return config;
  }
};

module.exports = nextConfig;