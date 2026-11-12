"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode } from "react";
import clsx from "clsx";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/upload", label: "Upload" },
  { href: "/findings", label: "Findings" },
  { href: "/report", label: "Reports" },
  { href: "/settings", label: "Settings" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_#e2e8f0_0%,_#f8fafc_45%,_#eef2ff_100%)] text-ink">
      <header className="border-b border-slate-200/80 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <p className="font-display text-2xl tracking-tight">AI Risk Investigator</p>
            <p className="text-xs text-slate-500">Audit · Compliance · Governance</p>
          </div>
          <nav className="flex gap-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  "rounded-md px-3 py-2 text-sm transition",
                  pathname === link.href
                    ? "bg-slatepanel text-white"
                    : "text-slate-600 hover:bg-slate-100",
                )}
              >
                {link.label}
              </Link>
            ))}
            <button
              className="ml-2 rounded-md px-3 py-2 text-sm text-slate-500 hover:bg-slate-100"
              onClick={() => {
                localStorage.removeItem("access_token");
                router.push("/login");
              }}
            >
              Sign out
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
