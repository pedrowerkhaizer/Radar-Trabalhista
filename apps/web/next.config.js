/** @type {import('next').NextConfig} */
const nextConfig = {
  // 'standalone' só para Docker: NEXT_STANDALONE=true next build
  // Não usar NODE_ENV porque 'next build' sempre seta NODE_ENV=production
  ...(process.env.NEXT_STANDALONE === 'true' ? { output: 'standalone' } : {}),
  reactStrictMode: true,
}
module.exports = nextConfig
