import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Temporarily disable to test double mounting
  // output: 'export', // Temporarily disabled - dynamic routes issue
  trailingSlash: true, // Use trailing slashes for better S3/CloudFront compatibility
  distDir: 'out', // Output directory for static files

  // Disable server-side features for static export
  experimental: {
    serverComponentsExternalPackages: [],
  },

  // Generate 404.html for SPA fallback
  generateBuildId: async () => {
    return 'spa-build';
  },

  // Note: rewrites() doesn't work with static export
  // API calls will be handled by environment variables instead
  images: {
    unoptimized: true,
    domains: [
      'images.unsplash.com',
      'localhost',
      '127.0.0.1',
      'picsum.photos',
      '14215678c021.ngrok-free.app',
    ],

    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/media/**',
      },
      {
        protocol: 'http',
        hostname: '127.0.0.1',
        port: '8000',
        pathname: '/media/**',
      },
      {
        protocol: 'https',
        hostname: 'localhost',
        port: '8000',
        pathname: '/media/**',
      },
      {
        protocol: 'https',
        hostname: '127.0.0.1',
        port: '8000',
        pathname: '/media/**',
      },
      // Add your production domain here when deploying
      // {
      //   protocol: 'https',
      //   hostname: 'your-production-domain.com',
      //   pathname: '/media/**',
      // },
    ],
  },
};

export default withNextIntl(nextConfig);
