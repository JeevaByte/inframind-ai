import Link from "next/link"

const footerGroups = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "/#features" },
      { label: "Pricing", href: "/pricing" },
      { label: "Documentation", href: "/documentation" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "/about" },
      { label: "Blog", href: "/blog" },
      { label: "Contact", href: "/contact" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy", href: "/privacy" },
      { label: "Terms", href: "/terms" },
    ],
  },
]

export function MarketingFooter() {
  return (
    <footer className="bg-slate-50 py-12 dark:bg-slate-900">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8 grid gap-8 md:grid-cols-4">
          <div>
            <h3 className="mb-4 font-bold text-slate-900 dark:text-white">
              InfraMind AI
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              AI-powered infrastructure analysis for DevOps and Cloud teams.
            </p>
          </div>

          {footerGroups.map((group) => (
            <div key={group.title}>
              <h4 className="mb-4 font-semibold text-slate-900 dark:text-white">
                {group.title}
              </h4>
              <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                {group.links.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} className="hover:text-slate-900 dark:hover:text-white">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-slate-200 pt-8 text-center text-sm text-slate-600 dark:border-slate-800 dark:text-slate-400">
          <p>&copy; {new Date().getFullYear()} InfraMind AI. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}