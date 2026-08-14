"use client";

import { CheckCircle2, LockKeyhole, Mail } from "lucide-react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
import { toast } from "sonner";

import { createClient } from "@/lib/supabase/client";

export function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const supabase = createClient();
    if (!supabase) {
      toast.error("Supabase is not configured for this deployment");
      return;
    }
    setLoading(true);
    const result = mode === "signup"
      ? await supabase.auth.signUp({ email, password, options: { data: { full_name: name } } })
      : await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (result.error) {
      toast.error(result.error.message);
      return;
    }
    if (mode === "signup" && !result.data.session) {
      toast.success("Check your inbox to confirm your account");
      return;
    }
    router.replace(searchParams.get("next") || "/meetings");
    router.refresh();
  }

  async function sendMagicLink() {
    const supabase = createClient();
    if (!supabase || !email) return;
    setLoading(true);
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/meetings` },
    });
    setLoading(false);
    if (error) toast.error(error.message);
    else toast.success("Magic link sent to your inbox");
  }

  function useDemoAccount() {
    setEmail("demo@echonote.app");
    setPassword("EchoNoteDemo#2026!");
    toast.success("Demo credentials added — sign in to explore the workspace.");
  }

  return (
    <main className="auth-page">
      <section className="auth-context">
        <div className="auth-brand"><Image src="/brand/echonote-logo-dark.svg" alt="EchoNote" width={156} height={40} priority /></div>
        <div className="auth-message"><p className="eyebrow">Your meeting memory</p><h1>Turn every conversation into work that moves forward.</h1><p>Searchable transcripts, reliable follow-ups, and a complete record of every decision.</p><ul><li><CheckCircle2 size={17} />Private workspace for every account</li><li><CheckCircle2 size={17} />Meeting notes ready in one place</li><li><CheckCircle2 size={17} />Tasks stay connected to context</li></ul></div>
        <small>Secure authentication and data isolation powered by Supabase.</small>
      </section>
      <section className="auth-form-panel">
        <form className="auth-form" onSubmit={submit}>
          <Image className="auth-form-logo" src="/brand/echonote-logo.svg" alt="EchoNote" width={156} height={40} priority />
          <div><p className="eyebrow">Welcome to EchoNote</p><h2>{mode === "signin" ? "Sign in to your workspace" : "Create your workspace"}</h2><p>{mode === "signin" ? "Continue where your conversations left off." : "Start with a private meeting library of your own."}</p></div>
          {mode === "signup" && <label>Full name<input required value={name} onChange={(event) => setName(event.target.value)} placeholder="Anusha Sharma" /></label>}
          <label>Email address<span className="auth-input"><Mail size={16} /><input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" /></span></label>
          <label>Password<span className="auth-input"><LockKeyhole size={16} /><input required minLength={8} type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" /></span></label>
          {mode === "signin" && <aside className="demo-account" aria-label="Demo account credentials"><div><span>Explore the demo workspace</span><strong>Ready-made meetings, transcripts, and follow-ups</strong></div><dl><div><dt>Email</dt><dd>demo@echonote.app</dd></div><div><dt>Password</dt><dd>EchoNoteDemo#2026!</dd></div></dl><button type="button" onClick={useDemoAccount}>Use demo credentials</button></aside>}
          <button className="button button-primary auth-submit" disabled={loading}>{loading ? "Please wait..." : mode === "signin" ? "Sign in" : "Create account"}</button>
          <div className="auth-divider"><span>or</span></div>
          <button type="button" className="button button-secondary auth-submit" onClick={sendMagicLink} disabled={loading || !email}><Mail size={16} />Email me a magic link</button>
          <p className="auth-switch">{mode === "signin" ? "New to EchoNote?" : "Already have an account?"}<button type="button" onClick={() => setMode(mode === "signin" ? "signup" : "signin")}>{mode === "signin" ? "Create account" : "Sign in"}</button></p>
        </form>
      </section>
    </main>
  );
}
