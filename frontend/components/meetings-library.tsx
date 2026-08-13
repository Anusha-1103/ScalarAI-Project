"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowDownUp, CalendarDays, ChevronRight, Filter, Plus, RefreshCw, Search, Users } from "lucide-react";
import Link from "next/link";
import { useDeferredValue, useMemo, useState } from "react";

import { AvatarStack } from "@/components/avatar-stack";
import { ImportMeetingDialog } from "@/components/import-meeting-dialog";
import { getMeetings } from "@/lib/api";
import { formatDuration, formatMeetingDate } from "@/lib/format";

export function MeetingsLibrary() {
  const [search, setSearch] = useState("");
  const [participant, setParticipant] = useState("");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const deferredSearch = useDeferredValue(search);
  const params = useMemo(() => {
    const value = new URLSearchParams({ sortOrder, limit: "50" });
    if (deferredSearch.trim()) value.set("search", deferredSearch.trim());
    if (participant.trim()) value.set("participant", participant.trim());
    if (dateFrom) value.set("dateFrom", new Date(`${dateFrom}T00:00:00`).toISOString());
    if (dateTo) value.set("dateTo", new Date(`${dateTo}T23:59:59`).toISOString());
    return value;
  }, [dateFrom, dateTo, deferredSearch, participant, sortOrder]);
  const meetings = useQuery({ queryKey: ["meetings", params.toString()], queryFn: () => getMeetings(params) });

  return (
    <section className="page meetings-page">
      <div className="page-heading">
        <div><p className="eyebrow">Your workspace</p><h1>Meetings</h1><p className="page-subtitle">Review conversations, decisions, and follow-ups.</p></div>
        <button className="button button-primary" onClick={() => setImportOpen(true)}><Plus size={17} />Add meeting</button>
      </div>

      <div className="library-toolbar">
        <label className="search-field"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search meeting titles or people" aria-label="Search meetings" /></label>
        <label className="filter-field"><Users size={16} /><input value={participant} onChange={(event) => setParticipant(event.target.value)} placeholder="Participant" aria-label="Filter by participant" /></label>
        <button className="toolbar-button" onClick={() => setSortOrder((value) => (value === "desc" ? "asc" : "desc"))}><ArrowDownUp size={16} />{sortOrder === "desc" ? "Newest" : "Oldest"}</button>
        <button className={`icon-button filter-more ${filtersOpen || dateFrom || dateTo ? "filter-active" : ""}`} title="Date filters" aria-label="Date filters" aria-expanded={filtersOpen} onClick={() => setFiltersOpen((value) => !value)}><Filter size={17} /></button>
      </div>

      {filtersOpen && <div className="date-filter-panel"><label>From<input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} /></label><label>To<input type="date" min={dateFrom || undefined} value={dateTo} onChange={(event) => setDateTo(event.target.value)} /></label><button className="button button-secondary" disabled={!dateFrom && !dateTo} onClick={() => { setDateFrom(""); setDateTo(""); }}>Clear dates</button></div>}

      <div className="library-summary"><span>{meetings.data?.pagination.totalItems ?? 0} meetings</span><span><CalendarDays size={15} />{dateFrom || dateTo ? "Custom date range" : "All time"}</span></div>

      <div className="meeting-list" aria-live="polite">
        {meetings.isLoading && Array.from({ length: 5 }, (_, index) => <div className="meeting-row meeting-skeleton" key={index} />)}
        {meetings.isError && (
          <div className="state-panel"><RefreshCw size={24} /><h2>Couldn&apos;t load meetings</h2><p>Check that the API is running, then try again.</p><button className="button button-secondary" onClick={() => meetings.refetch()}>Try again</button></div>
        )}
        {meetings.data?.items.length === 0 && (
          <div className="state-panel"><Search size={24} /><h2>No meetings found</h2><p>Adjust your search or participant filter.</p><button className="button button-secondary" onClick={() => { setSearch(""); setParticipant(""); }}>Clear filters</button></div>
        )}
        {meetings.data?.items.map((meeting) => (
          <Link href={`/meetings/${meeting.id}`} className="meeting-row" key={meeting.id}>
            <div className="meeting-icon"><span /></div>
            <div className="meeting-main"><h2>{meeting.title}</h2><p>{meeting.summaryPreview ?? "Transcript ready to review"}</p></div>
            <div className="meeting-people"><AvatarStack participants={meeting.participants} /><span>{meeting.participants.length} people</span></div>
            <div className="meeting-date"><strong>{formatMeetingDate(meeting.meetingAtUtc)}</strong><span>{formatDuration(meeting.durationInSeconds)}</span></div>
            <div className="meeting-actions"><span>{meeting.completedActionItemCount}/{meeting.actionItemCount} tasks</span><ChevronRight size={18} /></div>
          </Link>
        ))}
      </div>
      <ImportMeetingDialog open={importOpen} onClose={() => setImportOpen(false)} />
    </section>
  );
}
