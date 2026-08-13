"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, FileSearch, Search, X } from "lucide-react";
import Link from "next/link";
import { useDeferredValue, useEffect, useRef, useState } from "react";

import { globalSearch } from "@/lib/api";
import { formatMeetingDate, formatTimestamp } from "@/lib/format";

export function GlobalSearchDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query.trim());
  const results = useQuery({
    queryKey: ["global-search", deferredQuery],
    queryFn: () => globalSearch(deferredQuery),
    enabled: deferredQuery.length > 0,
  });
  useEffect(() => {
    if (open) window.setTimeout(() => inputRef.current?.focus(), 0);
  }, [open]);
  if (!open) return null;
  return (
    <div className="search-dialog-layer" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="search-dialog" role="dialog" aria-modal="true" aria-label="Search across meetings">
        <div className="search-dialog-input"><Search size={19} /><input ref={inputRef} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search every transcript" /><button className="icon-button" onClick={onClose} aria-label="Close search"><X size={18} /></button></div>
        <div className="search-results" aria-live="polite">
          {!deferredQuery && <div className="search-prompt"><FileSearch size={27} /><p>Search decisions, topics, and exact words across all meetings.</p></div>}
          {deferredQuery && results.isLoading && <div className="search-prompt"><span className="search-spinner" /><p>Searching transcripts...</p></div>}
          {results.data?.map((result) => <Link key={`${result.meetingId}-${result.segmentId}`} href={`/meetings/${result.meetingId}?t=${result.startInSeconds ?? 0}`} onClick={onClose} className="global-result"><div><strong>{result.meetingTitle}</strong><small>{formatMeetingDate(result.meetingAtUtc)} · {formatTimestamp(result.startInSeconds ?? 0)}</small><p>{result.snippet}</p></div><ArrowRight size={17} /></Link>)}
          {deferredQuery && results.data?.length === 0 && <div className="search-prompt"><FileSearch size={27} /><p>No transcript matches for &quot;{deferredQuery}&quot;.</p></div>}
        </div>
        <footer className="search-dialog-footer"><span><kbd>Enter</kbd> open result</span><span><kbd>Esc</kbd> close</span></footer>
      </section>
    </div>
  );
}
