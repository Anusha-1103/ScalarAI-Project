"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileText, Upload, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useRef, useState } from "react";
import { toast } from "sonner";

import { apiRequest } from "@/lib/api";
import { MeetingDetail } from "@/lib/types";

export function ImportMeetingDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [mode, setMode] = useState<"paste" | "file">("paste");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState("");

  const mutation = useMutation({
    mutationFn: async (form: HTMLFormElement) => {
      const data = new FormData(form);
      const names = String(data.get("participants") ?? "")
        .split(",")
        .map((name) => name.trim())
        .filter(Boolean);
      const tags = String(data.get("tags") ?? "")
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);
      if (mode === "file") {
        const upload = new FormData();
        upload.set("title", String(data.get("title")));
        upload.set("meetingAtUtc", new Date(String(data.get("meetingAtUtc"))).toISOString());
        upload.set("participantNames", JSON.stringify(names));
        upload.set("tagNames", JSON.stringify(tags));
        upload.set("transcriptFile", data.get("transcriptFile") as File);
        return apiRequest<MeetingDetail>("/meetings/import", { method: "POST", body: upload });
      }
      return apiRequest<MeetingDetail>("/meetings", {
        method: "POST",
        body: JSON.stringify({
          title: data.get("title"),
          meetingAtUtc: new Date(String(data.get("meetingAtUtc"))).toISOString(),
          participantNames: names,
          tags,
          transcript: data.get("transcript"),
        }),
      });
    },
    onSuccess: async (meeting) => {
      await queryClient.invalidateQueries({ queryKey: ["meetings"] });
      toast.success("Transcript is ready to review");
      onClose();
      router.push(`/meetings/${meeting.id}`);
    },
    onError: (error) => toast.error(error.message),
  });

  if (open && dialogRef.current && !dialogRef.current.open) dialogRef.current.showModal();
  if (!open && dialogRef.current?.open) dialogRef.current.close();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate(event.currentTarget);
  }

  async function handleFileChange(file: File | null) {
    setSelectedFile(file);
    setFilePreview("");
    if (!file) return;
    const text = await file.slice(0, 1_600).text();
    const readableLines = text.split(/\r?\n/).filter(Boolean);
    setFilePreview(readableLines.slice(0, 3).join(" ").slice(0, 240));
  }

  return (
    <dialog ref={dialogRef} className="modal" onCancel={onClose} onClose={onClose}>
      <div className="modal-heading">
        <div><p className="eyebrow">New meeting</p><h2>Add a transcript</h2></div>
        <button className="icon-button" type="button" onClick={onClose} aria-label="Close dialog"><X size={19} /></button>
      </div>
      <div className="segmented-control" role="tablist" aria-label="Transcript source">
        <button type="button" className={mode === "paste" ? "selected" : ""} onClick={() => setMode("paste")}><FileText size={16} />Paste</button>
        <button type="button" className={mode === "file" ? "selected" : ""} onClick={() => setMode("file")}><Upload size={16} />Upload</button>
      </div>
      <form onSubmit={handleSubmit} className="meeting-form">
        <label>Meeting title<input name="title" required minLength={2} placeholder="Weekly product sync" /></label>
        <div className="form-row">
          <label>Date and time<input name="meetingAtUtc" type="datetime-local" required /></label>
          <label>Participants<input name="participants" required placeholder="Anusha, Maya" /></label>
        </div>
        <label>Tags <span className="field-hint">Optional · separate with commas</span><input name="tags" maxLength={250} placeholder="Product, Customer, Weekly" /></label>
        {mode === "paste" ? (
          <label>Transcript<textarea name="transcript" required minLength={10} rows={9} placeholder={"Anusha: Let's review the launch plan.\nMaya: I will share the final checklist today."} /></label>
        ) : (
          <label className={`file-drop ${selectedFile ? "file-selected" : ""}`}>Transcript file<input name="transcriptFile" type="file" required accept=".txt,.vtt,.json" onChange={(event) => void handleFileChange(event.currentTarget.files?.[0] ?? null)} /><span>{selectedFile ? <><CheckCircle2 size={22} /><strong>{selectedFile.name}</strong><small>{Math.max(1, Math.ceil(selectedFile.size / 1024))} KB · ready to turn into timestamped dialogue</small>{filePreview && <em>{filePreview}</em>}</> : <><Upload size={22} /><strong>Choose a TXT, VTT, or JSON file</strong><small>We’ll turn this into a searchable, timestamped transcript.</small></>}</span></label>
        )}
        <div className="modal-actions">
          <button className="button button-secondary" type="button" onClick={onClose}>Cancel</button>
          <button className="button button-primary" type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Creating transcript…" : mode === "file" ? "Create transcript" : "Add meeting"}</button>
        </div>
      </form>
    </dialog>
  );
}
