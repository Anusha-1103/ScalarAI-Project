"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Clock3, ListChecks, RefreshCw, Users } from "lucide-react";
import Link from "next/link";

import { AvatarStack } from "@/components/avatar-stack";
import { getMeeting, getMeetings, getProfile } from "@/lib/api";
import { formatDuration, formatMeetingDate } from "@/lib/format";

export function DashboardWorkspace() {
  const profile = useQuery({ queryKey: ["profile"], queryFn: getProfile });
  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const library = await getMeetings(new URLSearchParams({ limit: "50", sortOrder: "desc" }));
      const details = await Promise.all(library.items.map((meeting) => getMeeting(meeting.id)));
      return { library, details };
    },
  });
  if (dashboard.isLoading) return <div className="page dashboard-loading"><div /><div /><div /></div>;
  if (!dashboard.data || dashboard.isError) return <div className="page state-panel"><RefreshCw size={24} /><h2>Dashboard unavailable</h2><button className="button button-primary" onClick={() => dashboard.refetch()}>Try again</button></div>;
  const { library, details } = dashboard.data;
  const totalSeconds = library.items.reduce((sum, meeting) => sum + meeting.durationInSeconds, 0);
  const actions = details.flatMap((meeting) => meeting.actionItems.map((item) => ({ ...item, meeting })));
  const openActions = actions.filter((item) => !item.isCompleted);
  const people = new Set(library.items.flatMap((meeting) => meeting.participants.map((person) => person.name)));
  const maxDuration = Math.max(...library.items.map((meeting) => meeting.durationInSeconds), 1);
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const accountName = profile.data?.displayName?.trim() || "there";
  return (
    <section className="page dashboard-page">
      <div className="page-heading"><div><p className="eyebrow">Workspace pulse</p><h1>{greeting}, {accountName}</h1><p className="page-subtitle">Here is what your conversations are moving forward.</p></div><Link className="button button-primary" href="/meetings">Open notebook<ArrowRight size={16} /></Link></div>
      <div className="metric-strip"><div><span className="metric-icon metric-purple"><Clock3 size={18} /></span><span><strong>{formatDuration(totalSeconds)}</strong><small>Conversation time</small></span></div><div><span className="metric-icon metric-green"><ListChecks size={18} /></span><span><strong>{openActions.length}</strong><small>Open action items</small></span></div><div><span className="metric-icon metric-gold"><Users size={18} /></span><span><strong>{people.size}</strong><small>People in meetings</small></span></div><div><span className="metric-icon metric-blue"><CheckCircle2 size={18} /></span><span><strong>{actions.length ? Math.round(((actions.length - openActions.length) / actions.length) * 100) : 0}%</strong><small>Task completion</small></span></div></div>
      <div className="dashboard-grid">
        <section className="dashboard-section"><header><div><p className="eyebrow">Recent activity</p><h2>Meeting volume</h2></div><span>Last {library.items.length} meetings</span></header><div className="meeting-chart">{library.items.slice().reverse().map((meeting) => <div key={meeting.id}><span style={{ height: `${Math.max((meeting.durationInSeconds / maxDuration) * 100, 16)}%` }} title={`${meeting.title}: ${formatDuration(meeting.durationInSeconds)}`} /><small>{new Date(meeting.meetingAtUtc).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</small></div>)}</div></section>
        <section className="dashboard-section"><header><div><p className="eyebrow">Needs attention</p><h2>Open follow-ups</h2></div><Link href="/meetings">View meetings</Link></header><div className="dashboard-task-list">{openActions.slice(0, 5).map((item) => <Link key={item.id} href={`/meetings/${item.meeting.id}`}><span className="task-dot" /><span><strong>{item.description}</strong><small>{item.meeting.title} · {item.assignee?.name ?? "Unassigned"}</small></span><ArrowRight size={15} /></Link>)}{!openActions.length && <div className="dashboard-empty"><CheckCircle2 size={22} />You are all caught up.</div>}</div></section>
      </div>
      <section className="dashboard-section recent-section"><header><div><p className="eyebrow">Notebook</p><h2>Recent meetings</h2></div><Link href="/meetings">View all</Link></header><div>{library.items.slice(0, 4).map((meeting) => <Link className="recent-meeting" key={meeting.id} href={`/meetings/${meeting.id}`}><AvatarStack participants={meeting.participants} /><span><strong>{meeting.title}</strong><small>{formatMeetingDate(meeting.meetingAtUtc)}</small></span><span>{meeting.actionItemCount} actions</span><ArrowRight size={16} /></Link>)}</div></section>
    </section>
  );
}
