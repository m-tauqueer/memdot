/** FSD-NAV-001 primary navigation order. */

export type NavItem = {
  href: string;
  label: string;
  match?: (pathname: string) => boolean;
};

export const PRIMARY_NAV: NavItem[] = [
  { href: "/today", label: "Today" },
  { href: "/library", label: "Library", match: (p) => p.startsWith("/library") },
  { href: "/spaces", label: "Spaces", match: (p) => p.startsWith("/spaces") },
  { href: "/ask", label: "Ask" },
  { href: "/test", label: "Test" },
  { href: "/review", label: "Review" },
  {
    href: "/memory/items",
    label: "Memory",
    match: (p) => p.startsWith("/memory"),
  },
  { href: "/integrations", label: "Integrations" },
  { href: "/settings", label: "Settings", match: (p) => p.startsWith("/settings") },
];

export const MOBILE_TAB_NAV: NavItem[] = PRIMARY_NAV.filter((item) =>
  ["Today", "Library", "Spaces", "Ask"].includes(item.label),
);

export function isNavActive(pathname: string, item: NavItem): boolean {
  if (item.match) {
    return item.match(pathname);
  }
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}
