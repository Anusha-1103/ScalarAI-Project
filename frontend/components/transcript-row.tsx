"use client";

import { Bookmark, Check, Pencil, X } from "lucide-react";
import { forwardRef, KeyboardEvent, useState } from "react";

import { formatTimestamp } from "@/lib/format";
import { splitHighlight } from "@/lib/transcript";
import { MeetingMoment, TranscriptSegment } from "@/lib/types";

interface TranscriptRowProps {
  segment: TranscriptSegment;
  moment?: MeetingMoment;
  active: boolean;
  hasMatch: boolean;
  hidden: boolean;
  query: string;
  onSeek: () => void;
  onSave: (text: string) => void;
  onToggleMoment: () => void;
}

export const TranscriptRow = forwardRef<HTMLDivElement, TranscriptRowProps>(function TranscriptRow(
  { segment, moment, active, hasMatch, hidden, query, onSeek, onSave, onToggleMoment },
  ref,
) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(segment.text);
  if (hidden) return null;
  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if ((event.key === "Enter" || event.key === " ") && event.target === event.currentTarget) onSeek();
  }
  function save() {
    const cleaned = text.trim();
    if (cleaned && cleaned !== segment.text) onSave(cleaned);
    setEditing(false);
  }
  return (
    <div
      ref={ref}
      role="button"
      tabIndex={0}
      className={`transcript-segment ${active ? "active" : ""} ${hasMatch ? "has-match" : ""}`}
      onClick={onSeek}
      onKeyDown={handleKeyDown}
    >
      <span className="speaker-avatar" style={{ background: segment.speaker?.avatarColor ?? "#7b8494" }}>{segment.speaker?.name.slice(0, 1).toUpperCase() ?? "?"}</span>
      <span className="segment-copy">
        <span className="segment-heading"><strong>{segment.speaker?.name ?? "Unknown speaker"}</strong><time>{formatTimestamp(segment.startInSeconds)}</time>{moment && <span className="saved-label"><Bookmark size={11} fill="currentColor" />Saved</span>}</span>
        {editing ? <span className="segment-editor" onClick={(event) => event.stopPropagation()}><textarea autoFocus value={text} onChange={(event) => setText(event.target.value)} /><span><button onClick={save} aria-label="Save transcript edit"><Check size={15} /></button><button onClick={() => { setText(segment.text); setEditing(false); }} aria-label="Cancel transcript edit"><X size={15} /></button></span></span> : <span className="segment-text">{splitHighlight(segment.text, query).map((part, index) => part.match ? <mark key={index}>{part.value}</mark> : <span key={index}>{part.value}</span>)}</span>}
      </span>
      {!editing && <span className="segment-tools" onClick={(event) => event.stopPropagation()}><button className={moment ? "selected" : ""} onClick={onToggleMoment} title={moment ? "Remove bookmark" : "Save moment"} aria-label={moment ? "Remove bookmark" : "Save moment"}><Bookmark size={15} fill={moment ? "currentColor" : "none"} /></button><button onClick={() => setEditing(true)} title="Edit transcript" aria-label="Edit transcript"><Pencil size={14} /></button></span>}
    </div>
  );
});
