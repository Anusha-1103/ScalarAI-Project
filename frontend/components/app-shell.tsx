"use client";

import {
  AudioLines,
  Bell,
  BookOpenText,
  CalendarDays,
  ChevronLeft,
  CircleHelp,
  LayoutDashboard,
  LogOut,
  Menu,
  Puzzle,
  Search,
  Settings,
  Sparkles,
  UserRound,
  Users,
  X,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { GlobalSearchDialog } from "@/components/global-search-dialog";
import { getProfile } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

const primaryNavigation = [
  { label: "Meetings", icon: BookOpenText, href: "/meetings" },
  { label: "Dashboard", icon: LayoutDashboard, href: "/dashboard", placeholder: true },
  { label: "Ask Echo", icon: Sparkles, href: "/ask", placeholder: true },
];

const secondaryNavigation = [
  { label: "Calendar", icon: CalendarDays, href: "/calendar" },
  { label: "People", icon: Users, href: "/team" },
  { label: "Integrations", icon: Puzzle, href: "/integrations" },
];

function getPageTitle(pathname: string) {
  if (pathname.startsWith("/meetings/")) return "Meeting workspace";
  if (pathname.startsWith("/meetings")) return "Meeting library";
  if (pathname.startsWith("/dashboard")) return "Dashboard";
  if (pathname.startsWith("/ask")) return "Ask Echo";
  if (pathname.startsWith("/calendar")) return "Calendar";
  if (pathname.startsWith("/team")) return "People";
  if (pathname.startsWith("/integrations")) return "Integrations";
  if (pathname.startsWith("/settings")) return "Settings";
  return "Workspace";
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);
  const profile = useQuery({
    queryKey: ["profile"],
    queryFn: getProfile,
    enabled: !pathname.startsWith("/auth"),
  });

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen(true);
      }
      if (event.key === "Escape") {
        setSearchOpen(false);
        setMobileOpen(false);
        setProfileMenuOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
    setProfileMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!mobileOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [mobileOpen]);

  useEffect(() => {
    const closeProfileMenu = (event: PointerEvent) => {
      if (!profileMenuRef.current?.contains(event.target as Node)) setProfileMenuOpen(false);
    };
    document.addEventListener("pointerdown", closeProfileMenu);
    return () => document.removeEventListener("pointerdown", closeProfileMenu);
  }, []);

  if (pathname.startsWith("/auth")) return children;

  if (profile.isLoading) {
    return <div className="workspace-boot" role="status"><span className="brand-mark"><AudioLines size={20} /></span><strong>Opening your workspace</strong></div>;
  }

  if (profile.isError) {
    return <div className="workspace-boot"><span className="brand-mark"><AudioLines size={20} /></span><strong>We couldn&apos;t open your workspace</strong><button className="button button-secondary" onClick={() => profile.refetch()}>Try again</button></div>;
  }

  const displayName = profile.data?.displayName?.trim() || "Your account";
  const initial = displayName.slice(0, 1).toUpperCase();

  async function signOut() {
    const supabase = createClient();
    if (!supabase) {
      toast.info("Demo workspace stays signed in");
      return;
    }
    await supabase.auth.signOut();
    window.location.assign("/auth/sign-in");
  }

  return (
    <div className="app-frame">
      <aside id="workspace-navigation" className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand-row">
          <Link href="/meetings" className="brand" aria-label="EchoNote meetings">
            <span className="brand-mark"><AudioLines size={19} strokeWidth={2.2} /></span>
            <span className="brand-copy"><strong>EchoNote</strong><small>Meeting intelligence</small></span>
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
          {secondaryNavigation.map(({ label, icon: Icon, href }) => (
            <Link className={`nav-item ${pathname.startsWith(href) ? "nav-item-active" : ""}`} href={href} key={label} onClick={() => setMobileOpen(false)}>
              <Icon size={18} />
              <span>{label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="nav-item" type="button" onClick={() => toast.info("Help center is coming soon")}><CircleHelp size={18} /><span>Help</span></button>
          <Link className={`nav-item ${pathname.startsWith("/settings") ? "nav-item-active" : ""}`} href="/settings"><Settings size={18} /><span>Settings</span></Link>
          <div className="profile-row">
            <span className="profile-avatar"><i />{initial}</span>
            <span className="profile-copy"><strong>{displayName}</strong><small>{profile.data?.isDemo ? "Demo workspace" : "Personal workspace"}</small></span>
            <button className="profile-signout" type="button" onClick={signOut} title="Sign out" aria-label="Sign out"><ChevronLeft size={16} /></button>
          </div>
        </div>
      </aside>

      {mobileOpen && <button className="sidebar-scrim" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}

      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation" aria-expanded={mobileOpen} aria-controls="workspace-navigation">
            <Menu size={20} />
          </button>
          <div className="topbar-context"><span>{profile.data?.isDemo ? "Demo workspace" : "Personal workspace"}</span><strong>{getPageTitle(pathname)}</strong></div>
          <button className="global-search" type="button" title="Global search" onClick={() => setSearchOpen(true)}>
            <Search size={17} /><span>Search across meetings</span><kbd>⌘ K</kbd>
          </button>
          <div className="topbar-actions">
            <button className="icon-button notification-button" title="Notifications" aria-label="Notifications" onClick={() => toast.success("You're all caught up")}><Bell size={18} /><i /></button>
            <div className="profile-menu-wrap" ref={profileMenuRef}>
              <button className="topbar-profile" type="button" title={displayName} aria-haspopup="menu" aria-expanded={profileMenuOpen} onClick={() => setProfileMenuOpen((open) => !open)}><span className="topbar-avatar">{initial}</span></button>
              {profileMenuOpen && <div className="profile-menu" role="menu"><div className="profile-menu-identity"><span className="topbar-avatar">{initial}</span><span><strong>{displayName}</strong><small>{profile.data?.email}</small></span></div><div className="profile-menu-status"><i />{profile.data?.isDemo ? "Demo workspace" : "Personal workspace"}</div><Link href="/settings" role="menuitem" onClick={() => setProfileMenuOpen(false)}><UserRound size={16} />Account settings</Link><button type="button" role="menuitem" onClick={signOut}><LogOut size={16} />Sign out</button></div>}
            </div>
          </div>
        </header>
        {children}
      </main>
      <GlobalSearchDialog open={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}
