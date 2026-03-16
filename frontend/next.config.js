/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    domains: ["picsum.photos"],
  },
};
module.exports = nextConfig;
