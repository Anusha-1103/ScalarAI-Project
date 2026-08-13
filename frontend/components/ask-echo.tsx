"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Bot, Search, Sparkles } from "lucide-react";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { globalSearch } from "@/lib/api";
import { formatMeetingDate, formatTimestamp } from "@/lib/format";

const suggestions = ["What did we decide about onboarding?", "Which risks were discussed?", "What follow-ups mention Friday?"];

export function AskEcho() {
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");
  const results = useQuery({ queryKey: ["ask-echo", query], queryFn: () => globalSearch(query), enabled: Boolean(query) });
  function ask(event: FormEvent) { event.preventDefault(); if (input.trim()) setQuery(input.trim()); }
  return (
    <section className="ask-page">
      <header className="ask-header"><span className="ask-logo"><Bot size={23} /></span><div><p className="eyebrow">Workspace intelligence</p><h1>Ask Echo</h1><p>Find answers grounded in your meeting transcripts.</p></div></header>
      <div className="ask-surface">
        {!query ? <div className="ask-welcome"><Sparkles size={28} /><h2>What do you need to know?</h2><p>Echo searches the conversations you can access and shows the source behind every answer.</p><div className="ask-suggestions">{suggestions.map((suggestion) => <button key={suggestion} onClick={() => { setInput(suggestion); setQuery(suggestion); }}>{suggestion}<ArrowRight size={15} /></button>)}</div></div> : <div className="ask-answer"><div className="user-question"><span>A</span><p>{query}</p></div><div className="echo-response"><span><Bot size={16} /></span><div><strong>Here is what I found</strong>{results.isLoading && <p>Searching your meeting memory...</p>}{results.data?.length === 0 && <p>I could not find matching evidence. Try names, topics, or exact phrases from the conversation.</p>}{results.data && results.data.length > 0 && <p>{results.data.slice(0, 3).map((item) => item.snippet).join(" ")}</p>}<div className="answer-sources">{results.data?.slice(0, 5).map((result) => <Link key={`${result.meetingId}-${result.segmentId}`} href={`/meetings/${result.meetingId}?t=${result.startInSeconds ?? 0}`}><span><strong>{result.meetingTitle}</strong><small>{formatMeetingDate(result.meetingAtUtc)} · {formatTimestamp(result.startInSeconds ?? 0)}</small></span><ArrowRight size={15} /></Link>)}</div></div></div></div>}
        <form className="ask-composer" onSubmit={ask}><Search size={18} /><textarea rows={1} value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask about decisions, objections, owners, or next steps" /><button className="button button-primary" disabled={!input.trim()}>Ask</button></form>
      </div>
    </section>
  );
}
