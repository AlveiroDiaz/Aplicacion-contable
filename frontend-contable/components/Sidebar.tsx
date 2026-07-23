"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  {
    href: "/",
    label: "Inicio",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    href: "/comprobantes/lista",
    label: "Comprobantes",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
  },
  {
    href: "/plan-cuentas",
    label: "Plan de Cuentas",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0">
        <line x1="8" y1="6" x2="21" y2="6" />
        <line x1="8" y1="12" x2="21" y2="12" />
        <line x1="8" y1="18" x2="21" y2="18" />
        <line x1="3" y1="6" x2="3.01" y2="6" />
        <line x1="3" y1="12" x2="3.01" y2="12" />
        <line x1="3" y1="18" x2="3.01" y2="18" />
      </svg>
    ),
  },
  {
    href: "/periodos/cerrar",
    label: "Cierre de Período",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
  },
  {
    href: "/reportes",
    label: "Reportes",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
  },
];

export function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const pathname = usePathname();

  return (
    <aside
      className={`fixed top-0 left-0 h-screen flex flex-col z-40 border-r transition-all duration-300 ${
        collapsed ? "w-16" : "w-64"
      }`}
      style={{
        backgroundColor: "var(--sidebar-bg)",
        color: "var(--sidebar-fg)",
        borderColor: "var(--sidebar-border)",
      }}
    >
      <div className="flex h-16 items-center border-b" style={{ borderColor: "var(--sidebar-border)" }}>
        {!collapsed ? (
          <>
            <button
              onClick={onToggle}
              className="flex items-center justify-center rounded-lg p-2 transition hover:bg-[var(--sidebar-hover)]"
              aria-label="Colapsar menú"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6 shrink-0">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <span className="ml-3 text-lg font-bold tracking-tight">Motor Contable</span>
          </>
        ) : (
          <button
            onClick={onToggle}
            className="mx-auto flex items-center justify-center rounded-lg p-2 transition hover:bg-[var(--sidebar-hover)]"
            aria-label="Expandir menú"
          >
            <span className="text-lg font-bold">M</span>
          </button>
        )}
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {items.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              className={`flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors gap-3 ${
                active ? "" : "hover:bg-[var(--sidebar-hover)]"
              }`}
              style={active ? { backgroundColor: "var(--sidebar-active)", color: "var(--sidebar-fg)" } : undefined}
            >
              {item.icon}
              {!collapsed && <span className="whitespace-nowrap">{item.label}</span>}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t text-xs" style={{ borderColor: "var(--sidebar-border)", color: "var(--sidebar-fg)", opacity: 0.6 }}>
        {!collapsed ? "Prueba técnica - Alveiro Diaz" : ""}
      </div>
    </aside>
  );
}
