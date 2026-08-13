"use client";

import {
  Bell,
  BookOpenText,
  Bot,
  CalendarDays,
  ChevronLeft,
  CircleHelp,
  LayoutDashboard,
  Menu,
  Puzzle,
  Search,
  Settings,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { GlobalSearchDialog } from "@/components/global-search-dialog";

const primaryNavigation = [
  { label: "Meetings", icon: BookOpenText, href: "/meetings" },
  { label: "Dashboard", icon: LayoutDashboard, href: "/dashboard", placeholder: true },
  { label: "Ask Echo", icon: Sparkles, href: "/ask", placeholder: true },
];

const secondaryNavigation = [
  { label: "Calendar", icon: CalendarDays },
  { label: "Team", icon: Users },
  { label: "Integrations", icon: Puzzle },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen(true);
      }
      if (event.key === "Escape") setSearchOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  return (
    <div className="app-frame">
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand-row">
          <Link href="/meetings" className="brand" aria-label="EchoNote meetings">
            <span className="brand-mark"><Bot size={19} strokeWidth={2.2} /></span>
            <span>EchoNote</span>
          </Link>
          <button className="icon-button sidebar-close" onClick={() => setMobileOpen(false)} aria-label="Close navigation">
            <X size={19} />
          </button>
        </div>

        <nav className="sidebar-nav" aria-label="Main navigation">
          {primaryNavigation.map(({ label, icon: Icon, href }) => (
            <Link
              href={href}
              key={label}
              className={`nav-item ${pathname.startsWith(href) ? "nav-item-active" : ""}`}
              onClick={() => setMobileOpen(false)}
            >
              <Icon size={18} />
              <span>{label}</span>
            </Link>
          ))}
          <p className="nav-label">Workspace</p>
          {secondaryNavigation.map(({ label, icon: Icon }) => (
            <button className="nav-item" key={label} type="button" title={`${label} — Coming soon`} onClick={() => toast.info(`${label} is coming soon`)}>
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="nav-item" type="button" onClick={() => toast.info("Help center is coming soon")}><CircleHelp size={18} /><span>Help</span></button>
          <button className="nav-item" type="button" onClick={() => toast.info("Settings are coming soon")}><Settings size={18} /><span>Settings</span></button>
          <div className="profile-row">
            <span className="profile-avatar">A</span>
            <span className="profile-copy"><strong>Anusha</strong><small>Personal workspace</small></span>
            <ChevronLeft size={16} />
          </div>
        </div>
      </aside>

      {mobileOpen && <button className="sidebar-scrim" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}

      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
            <Menu size={20} />
          </button>
          <button className="global-search" type="button" title="Global search" onClick={() => setSearchOpen(true)}>
            <Search size={17} /><span>Search across meetings</span><kbd>⌘ K</kbd>
          </button>
          <div className="topbar-actions">
            <button className="icon-button" aria-label="Notifications"><Bell size={19} /></button>
            <span className="topbar-avatar">A</span>
          </div>
        </header>
        {children}
      </main>
      <GlobalSearchDialog open={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}
