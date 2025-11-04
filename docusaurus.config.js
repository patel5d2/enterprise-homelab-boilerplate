module.exports = {
  title: 'All Projects Documentation',
  tagline: 'Aggregated documentation for all GitHub projects',
  url: 'https://patel5d2.github.io',
  baseUrl: '/enterprise-homelab-boilerplate/',
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'patel5d2',
  projectName: 'enterprise-homelab-boilerplate',
  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          path: 'docs',
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/patel5d2/enterprise-homelab-boilerplate/edit/main/',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],
  themeConfig: {
    navbar: {
      title: 'Project Docs',
      items: [
        {
          href: 'https://github.com/patel5d2',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [],
      copyright: `Copyright © ${new Date().getFullYear()} patel5d2. Built with Docusaurus.`,
    },
  },
};