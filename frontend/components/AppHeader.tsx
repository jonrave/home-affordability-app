import type { ReactNode } from "react";

type AppHeaderProps = {
  active: "overview" | "liquidity" | "monte-carlo";
  actions?: ReactNode;
  eyebrow?: string;
  title?: string;
};

const links = [
  { id: "overview", label: "Overview", href: "/", hint: "Decision summary and guided assumptions" },
  { id: "liquidity", label: "Liquidity", href: "/liquidity", hint: "Year-by-year cash flow and reserves" },
  { id: "monte-carlo", label: "Monte Carlo", href: "/monte-carlo", hint: "Seeded simulation risk view" }
] as const;

export function AppHeader({
  active,
  actions,
  eyebrow = "Household Finance",
  title = "Home Affordability"
}: AppHeaderProps) {
  return (
    <header className="topbar">
      <div className="topbar-title">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
        </div>
        <nav aria-label="Model detail views" className="nav-links">
          {links.map((link) => (
            <a
              aria-current={active === link.id ? "page" : undefined}
              className={active === link.id ? "active" : undefined}
              href={link.href}
              key={link.id}
              title={link.hint}
            >
              {link.label}
            </a>
          ))}
        </nav>
        <p className="nav-helper">Start with the decision brief, then audit the year-by-year liquidity path and simulation risk.</p>
      </div>
      {actions ? <div className="topbar-actions">{actions}</div> : null}
    </header>
  );
}
