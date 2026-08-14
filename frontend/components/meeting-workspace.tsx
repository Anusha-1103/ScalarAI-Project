"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  BarChart3,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Circle,
  Clock3,
  Download,
  ListChecks,
  MoreHorizontal,
  Pause,
  Pencil,
  Play,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Tag,
  Trash2,
  Users,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { AvatarStack } from "@/components/avatar-stack";
import { TranscriptRow } from "@/components/transcript-row";
import {
  createMeetingMoment,
  createActionItem,
  deleteActionItem,
  deleteMeeting,
  deleteMeetingMoment,
  getMeeting,
  updateActionItem,
  updateMeeting,
  updateTranscriptSegment,
} from "@/lib/api";
import { formatMeetingDate, formatTimestamp } from "@/lib/format";
import { buildMeetingInsights, matchesSmartFilter, SmartFilter } from "@/lib/meeting-insights";
import { findActiveSegmentIndex, transcriptMatchIndexes } from "@/lib/transcript";
import { ActionItem, MeetingDetail } from "@/lib/types";

type DetailTab = "summary" | "actions" | "chapters" | "insights";

function formatSourceType(sourceType: string) {
  return sourceType.replaceAll("_", " ").replaceAll("-", " ");
}

function Player({
  duration,
  currentTime,
  playing,
  onPlayingChange,
  onSeek,
}: {
  duration: number;
  currentTime: number;
  playing: boolean;
  onPlayingChange: (value: boolean) => void;
  onSeek: (value: number) => void;
}) {
  const progress = duration ? Math.min((currentTime / duration) * 100, 100) : 0;
  return (
    <div className="meeting-player">
      <button
        className="player-toggle"
        type="button"
        onClick={() => onPlayingChange(!playing)}
        aria-label={playing ? "Pause recording" : "Play recording"}
      >
        {playing ? <Pause size={17} fill="currentColor" /> : <Play size={17} fill="currentColor" />}
      </button>
      <span className="player-time">{formatTimestamp(currentTime)}</span>
      <label className="player-progress" style={{ "--progress": `${progress}%` } as React.CSSProperties}>
        <span className="sr-only">Recording position</span>
        <input
          type="range"
          min="0"
          max={Math.max(duration, 1)}
          step="0.1"
          value={Math.min(currentTime, duration)}
          onChange={(event) => onSeek(Number(event.target.value))}
        />
      </label>
      <span className="player-time">{formatTimestamp(duration)}</span>
      <button className="icon-button player-menu" type="button" title="Playback options" aria-label="Playback options">
        <MoreHorizontal size={18} />
      </button>
    </div>
  );
}

function ActionRow({
  item,
  onToggle,
  onDelete,
  onEdit,
  busy,
}: {
  item: ActionItem;
  onToggle: () => void;
  onDelete: () => void;
  onEdit: (description: string) => void;
  busy: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [description, setDescription] = useState(item.description);
  function submit(event: { preventDefault(): void }) {
    event.preventDefault();
    if (description.trim() && description.trim() !== item.description) onEdit(description.trim());
    setEditing(false);
  }
  return (
    <div className={`action-row ${item.isCompleted ? "action-complete" : ""}`}>
      <button type="button" className="task-check" onClick={onToggle} disabled={busy} aria-label={item.isCompleted ? "Mark incomplete" : "Mark complete"}>
        {item.isCompleted ? <CheckCircle2 size={19} /> : <Circle size={19} />}
      </button>
      <div className="action-copy">
        {editing ? <form className="action-edit-form" onSubmit={submit}><input autoFocus value={description} onChange={(event) => setDescription(event.target.value)} onBlur={submit} aria-label="Action item description" /></form> : <span>{item.description}</span>}
        <small>{item.assignee?.name ?? "Unassigned"}{item.dueAtUtc ? ` · Due ${new Date(item.dueAtUtc).toLocaleDateString()}` : ""}</small>
      </div>
      <button type="button" className="icon-button row-edit" onClick={() => setEditing(true)} disabled={busy} aria-label="Edit action item"><Pencil size={14} /></button>
      <button type="button" className="icon-button row-delete" onClick={onDelete} disabled={busy} aria-label="Delete action item"><Trash2 size={15} /></button>
    </div>
  );
}

function EditMeetingDialog({ meeting, onClose }: { meeting: MeetingDetail; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState(meeting.title);
  const [date, setDate] = useState(new Date(meeting.meetingAtUtc).toISOString().slice(0, 16));
  const [participants, setParticipants] = useState(meeting.participants.map((person) => person.name).join(", "));
  const [tags, setTags] = useState(meeting.tags.join(", "));
  const mutation = useMutation({
    mutationFn: () => updateMeeting(meeting.id, {
      title: title.trim(),
      meetingAtUtc: new Date(date).toISOString(),
      participantNames: participants.split(",").map((name) => name.trim()).filter(Boolean),
      tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
    }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["meeting", meeting.id], updated);
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      toast.success("Meeting details updated");
      onClose();
    },
    onError: (error) => toast.error(error.message),
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  return (
    <div className="dialog-layer" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="inline-dialog" role="dialog" aria-modal="true" aria-labelledby="edit-title">
        <header><div><p className="eyebrow">Meeting settings</p><h2 id="edit-title">Edit details</h2></div><button className="icon-button" onClick={onClose} aria-label="Close"><X size={18} /></button></header>
        <form className="meeting-form" onSubmit={submit}>
          <label>Title<input required minLength={2} value={title} onChange={(event) => setTitle(event.target.value)} /></label>
          <label>Date and time<input required type="datetime-local" value={date} onChange={(event) => setDate(event.target.value)} /></label>
          <label>Participants<input required value={participants} onChange={(event) => setParticipants(event.target.value)} /><span className="field-hint">Separate names with commas</span></label>
          <label>Tags<input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="Product, Weekly" /><span className="field-hint">Optional · separate tags with commas</span></label>
          <div className="modal-actions"><button type="button" className="button button-secondary" onClick={onClose}>Cancel</button><button className="button button-primary" disabled={mutation.isPending}><Check size={16} />Save changes</button></div>
        </form>
      </section>
    </div>
  );
}

export function MeetingWorkspace({ meetingId }: { meetingId: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const meetingQuery = useQuery({ queryKey: ["meeting", meetingId], queryFn: () => getMeeting(meetingId) });
  const meeting = meetingQuery.data;
  const [tab, setTab] = useState<DetailTab>("summary");
  const [mobilePane, setMobilePane] = useState<"notes" | "transcript">("notes");
  const [currentTime, setCurrentTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [transcriptSearch, setTranscriptSearch] = useState("");
  const [smartFilter, setSmartFilter] = useState<SmartFilter>("all");
  const [matchPosition, setMatchPosition] = useState(0);
  const [newAction, setNewAction] = useState("");
  const [editOpen, setEditOpen] = useState(false);
  const segmentRefs = useRef<(HTMLDivElement | null)[]>([]);

  const segments = useMemo(() => meeting?.transcriptSegments ?? [], [meeting?.transcriptSegments]);
  const duration = meeting?.durationInSeconds ?? 0;
  const activeIndex = useMemo(() => findActiveSegmentIndex(segments, currentTime), [segments, currentTime]);
  const matches = useMemo(() => transcriptMatchIndexes(segments, transcriptSearch), [segments, transcriptSearch]);
  const insights = useMemo(() => buildMeetingInsights(segments), [segments]);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setCurrentTime((time) => {
        if (time + 0.25 >= duration) {
          setPlaying(false);
          return duration;
        }
        return time + 0.25;
      });
    }, 250);
    return () => window.clearInterval(timer);
  }, [duration, playing]);

  useEffect(() => {
    if (playing && activeIndex >= 0) segmentRefs.current[activeIndex]?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [activeIndex, playing]);

  useEffect(() => setMatchPosition(0), [transcriptSearch]);

  useEffect(() => {
    const requestedTime = Number(searchParams.get("t"));
    if (Number.isFinite(requestedTime) && requestedTime > 0 && duration) setCurrentTime(Math.min(requestedTime, duration));
  }, [duration, searchParams]);

  const refreshMeeting = () => queryClient.invalidateQueries({ queryKey: ["meeting", meetingId] });
  const actionMutation = useMutation({
    mutationFn: ({ id, completed, description }: { id: string; completed?: boolean; description?: string }) => updateActionItem(id, { isCompleted: completed, description }),
    onSuccess: refreshMeeting,
    onError: (error) => toast.error(error.message),
  });
  const removeActionMutation = useMutation({
    mutationFn: deleteActionItem,
    onSuccess: () => { refreshMeeting(); toast.success("Action item removed"); },
    onError: (error) => toast.error(error.message),
  });
  const createActionMutation = useMutation({
    mutationFn: (description: string) => createActionItem(meetingId, { description }),
    onSuccess: () => { setNewAction(""); refreshMeeting(); toast.success("Action item added"); },
    onError: (error) => toast.error(error.message),
  });
  const deleteMeetingMutation = useMutation({
    mutationFn: () => deleteMeeting(meetingId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["meetings"] }); router.push("/meetings"); toast.success("Meeting deleted"); },
    onError: (error) => toast.error(error.message),
  });
  const transcriptMutation = useMutation({
    mutationFn: ({ id, text }: { id: string; text: string }) => updateTranscriptSegment(id, text),
    onSuccess: () => { refreshMeeting(); toast.success("Transcript updated"); },
    onError: (error) => toast.error(error.message),
  });
  const momentMutation = useMutation({
    mutationFn: async ({ segmentId, momentId }: { segmentId: string; momentId?: string }) => {
      if (momentId) await deleteMeetingMoment(momentId);
      else await createMeetingMoment(meetingId, segmentId);
    },
    onSuccess: () => { refreshMeeting(); toast.success("Saved moments updated"); },
    onError: (error) => toast.error(error.message),
  });

  function seek(seconds: number) {
    setCurrentTime(Math.min(Math.max(seconds, 0), duration));
  }

  function moveMatch(direction: 1 | -1) {
    if (!matches.length) return;
    const next = (matchPosition + direction + matches.length) % matches.length;
    setMatchPosition(next);
    const segmentIndex = matches[next];
    seek(segments[segmentIndex].startInSeconds);
    segmentRefs.current[segmentIndex]?.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  function exportNotes() {
    if (!meeting) return;
    const content = [`# ${meeting.title}`, "", meeting.summary?.overview ?? "", "", "## Key points", ...(meeting.summary?.keyPoints.map((point) => `- ${point}`) ?? []), "", "## Action items", ...meeting.actionItems.map((item) => `- [${item.isCompleted ? "x" : " "}] ${item.description}`)].join("\n");
    const url = URL.createObjectURL(new Blob([content], { type: "text/markdown" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${meeting.title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.md`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success("Meeting notes exported");
  }

  if (meetingQuery.isLoading) return <div className="detail-loading"><div className="detail-loading-bar" /><div className="detail-loading-grid"><div /><div /></div></div>;
  if (meetingQuery.isError || !meeting) return <div className="page state-panel"><RefreshCw size={25} /><h2>Meeting unavailable</h2><p>It may have been removed, or the API is not responding.</p><div className="state-actions"><Link className="button button-secondary" href="/meetings"><ArrowLeft size={16} />Back to meetings</Link><button className="button button-primary" onClick={() => meetingQuery.refetch()}>Try again</button></div></div>;

  return (
    <div className="meeting-detail-page">
      <header className="meeting-detail-header">
        <Link className="icon-button" href="/meetings" aria-label="Back to meetings"><ArrowLeft size={19} /></Link>
        <div className="meeting-title-block"><div className="meeting-title-kicker"><span><Sparkles size={11} />AI notes ready</span><span>{formatSourceType(meeting.sourceType)}</span>{meeting.tags.map((tag) => <span className="meeting-tag" key={tag}><Tag size={10} />{tag}</span>)}</div><h1>{meeting.title}</h1><div className="meeting-meta"><span><CalendarDays size={14} />{formatMeetingDate(meeting.meetingAtUtc)}</span><span><Clock3 size={14} />{formatTimestamp(meeting.durationInSeconds)}</span><span><Users size={14} />{meeting.participants.length} attendees</span></div></div>
        <AvatarStack participants={meeting.participants} />
        <button className="button button-secondary detail-action" type="button" onClick={exportNotes}><Download size={16} />Export</button>
        <button className="icon-button detail-action" type="button" title="Edit meeting" aria-label="Edit meeting" onClick={() => setEditOpen(true)}><Pencil size={16} /></button>
        <button className="icon-button detail-action danger-button" type="button" title="Delete meeting" aria-label="Delete meeting" onClick={() => window.confirm("Delete this meeting and its notes?") && deleteMeetingMutation.mutate()}><Trash2 size={16} /></button>
      </header>

      <nav className="mobile-pane-switch" aria-label="Meeting workspace panels">
        <button className={mobilePane === "notes" ? "active" : ""} onClick={() => setMobilePane("notes")}><Sparkles size={15} />Notes</button>
        <button className={mobilePane === "transcript" ? "active" : ""} onClick={() => setMobilePane("transcript")}><ListChecks size={15} />Transcript</button>
      </nav>
      <div className="meeting-detail-grid">
        <section className={`insights-panel ${mobilePane !== "notes" ? "mobile-pane-hidden" : ""}`} aria-label="Meeting insights">
          <nav className="detail-tabs" aria-label="Meeting detail sections">
            <button className={tab === "summary" ? "active" : ""} onClick={() => setTab("summary")}><Sparkles size={15} />Summary</button>
            <button className={tab === "actions" ? "active" : ""} onClick={() => setTab("actions")}><ListChecks size={15} />Actions <span>{meeting.actionItems.length}</span></button>
            <button className={tab === "chapters" ? "active" : ""} onClick={() => setTab("chapters")}><ChevronDown size={15} />Chapters</button>
            <button className={tab === "insights" ? "active" : ""} onClick={() => setTab("insights")}><BarChart3 size={15} />Insights</button>
          </nav>

          <div className="insights-scroll">
            {tab === "summary" && <div className="summary-content"><div className="section-heading"><span className="summary-icon"><Sparkles size={17} /></span><div><p className="eyebrow">AI meeting notes</p><h2>Conversation summary</h2></div></div><div className="summary-overview"><span>Executive brief</span><p className="overview">{meeting.summary?.overview ?? "No summary is available for this meeting."}</p></div><div className="content-label"><h3>Key points</h3><span>{meeting.summary?.keyPoints.length ?? 0} signals</span></div><ul className="key-points">{meeting.summary?.keyPoints.map((point, index) => <li key={point}><span>{String(index + 1).padStart(2, "0")}</span>{point}</li>)}</ul></div>}

            {tab === "actions" && <div className="actions-content"><div className="section-heading"><span className="actions-icon"><ListChecks size={17} /></span><div><p className="eyebrow">Follow-through</p><h2>Action items</h2></div></div><div className="action-progress-summary"><span><strong>{meeting.actionItems.filter((item) => item.isCompleted).length}</strong> completed</span><span className="action-progress-track"><i style={{ width: `${meeting.actionItems.length ? (meeting.actionItems.filter((item) => item.isCompleted).length / meeting.actionItems.length) * 100 : 0}%` }} /></span><span>{meeting.actionItems.length} total</span></div><form className="new-action" onSubmit={(event) => { event.preventDefault(); if (newAction.trim()) createActionMutation.mutate(newAction.trim()); }}><input value={newAction} onChange={(event) => setNewAction(event.target.value)} placeholder="Add an action item" aria-label="New action item" /><button className="icon-button" disabled={!newAction.trim() || createActionMutation.isPending} aria-label="Add action item"><Plus size={18} /></button></form><div className="action-list">{meeting.actionItems.map((item) => <ActionRow key={item.id} item={item} busy={actionMutation.isPending || removeActionMutation.isPending} onToggle={() => actionMutation.mutate({ id: item.id, completed: !item.isCompleted })} onEdit={(description) => actionMutation.mutate({ id: item.id, description })} onDelete={() => removeActionMutation.mutate(item.id)} />)}{!meeting.actionItems.length && <div className="mini-empty"><CheckCircle2 size={24} /><p>No open action items.</p></div>}</div></div>}

            {tab === "chapters" && <div className="chapters-content"><div className="section-heading"><span className="chapters-icon"><ChevronDown size={17} /></span><div><p className="eyebrow">Recording outline</p><h2>Chapters</h2></div></div><div className="chapter-list">{meeting.chapters.map((chapter, index) => <button key={chapter.id} onClick={() => seek(chapter.startInSeconds)}><span className="chapter-number">{String(index + 1).padStart(2, "0")}</span><span className="chapter-copy"><strong>{chapter.title}</strong><small>{formatTimestamp(chapter.startInSeconds)}</small></span><Play size={15} /></button>)}</div></div>}

            {tab === "insights" && <div className="analytics-content"><div className="section-heading"><span className="analytics-icon"><BarChart3 size={17} /></span><div><p className="eyebrow">Conversation intelligence</p><h2>Meeting analytics</h2></div></div><div className="analytics-stats"><div><strong>{insights.sentiment}</strong><span>Conversation tone</span></div><div><strong>{insights.questions}</strong><span>Questions</span></div><div><strong>{meeting.moments.length}</strong><span>Saved moments</span></div></div><h3>Speaker talk time</h3><div className="speaker-bars">{insights.speakers.map((speaker, index) => <div key={speaker.name}><span><strong>{speaker.name}</strong><small>{speaker.percent}%</small></span><span className="speaker-bar"><i style={{ width: `${speaker.percent}%`, background: meeting.participants.find((person) => person.name === speaker.name)?.avatarColor ?? (index % 2 ? "#159979" : "#5b5bd6") }} /></span></div>)}</div><h3>Top topics</h3><div className="topic-cloud">{insights.topics.map((topic) => <button key={topic.word} onClick={() => { setTranscriptSearch(topic.word); setMobilePane("transcript"); }}>{topic.word}<span>{topic.count}</span></button>)}</div></div>}
          </div>
        </section>

        <section className={`transcript-panel ${mobilePane !== "transcript" ? "mobile-pane-hidden" : ""}`} aria-label="Transcript">
          <header className="transcript-header"><div><p className="eyebrow">Full conversation</p><h2>Transcript</h2></div><div className="transcript-search"><Search size={16} /><input value={transcriptSearch} onChange={(event) => setTranscriptSearch(event.target.value)} placeholder="Find in transcript" aria-label="Find in transcript" />{transcriptSearch && <><span>{matches.length ? `${matchPosition + 1}/${matches.length}` : "0/0"}</span><button onClick={() => moveMatch(-1)} disabled={!matches.length} aria-label="Previous match"><ChevronLeft size={16} /></button><button onClick={() => moveMatch(1)} disabled={!matches.length} aria-label="Next match"><ChevronRight size={16} /></button><button onClick={() => setTranscriptSearch("")} aria-label="Clear transcript search"><X size={15} /></button></>}</div></header>
          <div className="smart-filters" role="group" aria-label="Smart transcript filters">{(["all", "questions", "tasks", "metrics"] as SmartFilter[]).map((filter) => <button key={filter} className={smartFilter === filter ? "active" : ""} onClick={() => setSmartFilter(filter)}>{filter === "all" ? `All ${segments.length}` : `${filter[0].toUpperCase()}${filter.slice(1)} ${insights[filter]}`}</button>)}</div>
          <div className="transcript-list">{segments.map((segment, index) => <TranscriptRow ref={(node) => { segmentRefs.current[index] = node; }} key={segment.id} segment={segment} moment={meeting.moments.find((item) => item.segmentId === segment.id)} active={index === activeIndex} hasMatch={matches.includes(index)} hidden={!matchesSmartFilter(segment, smartFilter)} query={transcriptSearch} onSeek={() => seek(segment.startInSeconds)} onSave={(text) => transcriptMutation.mutate({ id: segment.id, text })} onToggleMoment={() => { const moment = meeting.moments.find((item) => item.segmentId === segment.id); momentMutation.mutate({ segmentId: segment.id, momentId: moment?.id }); }} />)}</div>
          <Player duration={duration} currentTime={currentTime} playing={playing} onPlayingChange={setPlaying} onSeek={seek} />
        </section>
      </div>
      {editOpen && <EditMeetingDialog meeting={meeting} onClose={() => setEditOpen(false)} />}
    </div>
  );
}
