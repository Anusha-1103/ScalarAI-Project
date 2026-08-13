"use client";

import { useQuery } from "@tanstack/react-query";
import { CalendarDays, Check, ExternalLink, Link2, Settings2, Users } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { getMeetings, getProfile } from "@/lib/api";
import { formatDuration, formatMeetingDate } from "@/lib/format";
import { MeetingListItem } from "@/lib/types";

export function CalendarWorkspace() {
  const meetings = useQuery({ queryKey: ["calendar-meetings"], queryFn: () => getMeetings(new URLSearchParams({ limit: "50", sortOrder: "desc" })) });
  const meetingItems = meetings.data?.items;
  const groups = useMemo(() => {
    const values = new Map<string, MeetingListItem[]>();
    meetingItems?.forEach((meeting) => {
      const key = new Date(meeting.meetingAtUtc).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
      values.set(key, [...(values.get(key) ?? []), meeting]);
    });
    return [...values.entries()];
  }, [meetingItems]);
  return <section className="page workspace-page"><div className="page-heading"><div><p className="eyebrow">Schedule history</p><h1>Calendar</h1><p className="page-subtitle">Browse conversations in the context of when they happened.</p></div></div><div className="agenda-layout"><aside><CalendarDays size={19} /><strong>{new Date().toLocaleDateString(undefined, { month: "long", year: "numeric" })}</strong><p>{meetings.data?.items.length ?? 0} recorded meetings</p></aside><div className="agenda-list">{groups.map(([date, items]) => <section key={date}><h2>{date}</h2>{items.map((meeting) => <Link key={meeting.id} href={`/meetings/${meeting.id}`}><time>{new Date(meeting.meetingAtUtc).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}</time><span><strong>{meeting.title}</strong><small>{meeting.participants.map((person) => person.name).join(", ")}</small></span><span>{formatDuration(meeting.durationInSeconds)}</span></Link>)}</section>)}</div></div></section>;
}

export function TeamWorkspace() {
  const meetings = useQuery({ queryKey: ["team-meetings"], queryFn: () => getMeetings(new URLSearchParams({ limit: "50" })) });
  const people = useMemo(() => {
    const values = new Map<string, { name: string; color: string; meetings: number; lastMeeting: string }>();
    meetings.data?.items.forEach((meeting) => meeting.participants.forEach((person) => {
      const current = values.get(person.name);
      values.set(person.name, { name: person.name, color: person.avatarColor, meetings: (current?.meetings ?? 0) + 1, lastMeeting: current?.lastMeeting && current.lastMeeting > meeting.meetingAtUtc ? current.lastMeeting : meeting.meetingAtUtc });
    }));
    return [...values.values()].sort((a, b) => b.meetings - a.meetings);
  }, [meetings.data]);
  return <section className="page workspace-page"><div className="page-heading"><div><p className="eyebrow">Conversation network</p><h1>People</h1><p className="page-subtitle">Everyone who appears in your accessible meeting history.</p></div><button className="button button-secondary" onClick={() => toast.info("Workspace invitations require email delivery configuration")}><Users size={16} />Invite teammate</button></div><div className="people-table"><header><span>Person</span><span>Meetings</span><span>Last conversation</span></header>{people.map((person) => <div key={person.name}><span className="person-name"><i style={{ background: person.color }}>{person.name.slice(0, 1)}</i><strong>{person.name}</strong></span><span>{person.meetings}</span><span>{formatMeetingDate(person.lastMeeting)}</span></div>)}</div></section>;
}

const integrations = [
  ["Google Meet", "Capture scheduled Meet conversations", "GM"],
  ["Zoom", "Import cloud recordings and transcripts", "Z"],
  ["Microsoft Teams", "Sync meetings from your Microsoft calendar", "MT"],
  ["Slack", "Send summaries and action items to channels", "S"],
  ["Notion", "Publish meeting notes to your knowledge base", "N"],
  ["HubSpot", "Attach conversation context to CRM records", "H"],
] as const;

export function IntegrationsWorkspace() {
  const [connected, setConnected] = useState<string[]>([]);
  return <section className="page workspace-page"><div className="page-heading"><div><p className="eyebrow">Connected workflow</p><h1>Integrations</h1><p className="page-subtitle">Choose where meetings come from and where notes go next.</p></div></div><div className="integration-grid">{integrations.map(([name, description, mark]) => { const active = connected.includes(name); return <article key={name}><span className="integration-mark">{mark}</span><div><h2>{name}</h2><p>{description}</p></div><button className={`button ${active ? "button-secondary connected-button" : "button-primary"}`} onClick={() => { setConnected((items) => active ? items.filter((item) => item !== name) : [...items, name]); toast.success(active ? `${name} disconnected` : `${name} connection staged`); }}>{active ? <><Check size={15} />Connected</> : <><Link2 size={15} />Connect</>}</button></article>; })}</div><p className="integration-note"><ExternalLink size={14} />Provider OAuth credentials are required before staged connections can exchange production data.</p></section>;
}

export function SettingsWorkspace() {
  const profile = useQuery({ queryKey: ["profile"], queryFn: getProfile });
  return <section className="page workspace-page"><div className="page-heading"><div><p className="eyebrow">Personal workspace</p><h1>Settings</h1><p className="page-subtitle">Manage your account and meeting preferences.</p></div></div><div className="settings-layout"><nav><button className="active"><Settings2 size={16} />General</button></nav><section><h2>Profile</h2><div className="settings-profile"><span>{profile.data?.displayName.slice(0, 1) ?? "A"}</span><div><strong>{profile.data?.displayName ?? "Anusha"}</strong><small>{profile.data?.email ?? "anusha@echonote.local"}</small></div></div><label>Workspace name<input defaultValue={`${profile.data?.displayName ?? "Anusha"}'s workspace`} /></label><label>Default meeting visibility<select defaultValue="private"><option value="private">Only me</option><option value="participants">Meeting participants</option></select></label><div className="settings-status"><Check size={16} /><span><strong>{profile.data?.isDemo ? "Local demo mode" : "Supabase account active"}</strong><small>{profile.data?.isDemo ? "Configure Supabase environment variables to enable real accounts." : "Authentication and account isolation are enabled."}</small></span></div><button className="button button-primary" onClick={() => toast.success("Preferences saved")}>Save preferences</button></section></div></section>;
}
