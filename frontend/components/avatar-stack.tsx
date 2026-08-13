import { Participant } from "@/lib/types";

export function Avatar({ participant, size = "md" }: { participant: Participant; size?: "sm" | "md" }) {
  const initials = participant.name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("");
  return (
    <span
      className={`avatar ${size === "sm" ? "avatar-sm" : ""}`}
      style={{ backgroundColor: participant.avatarColor }}
      title={participant.name}
      aria-label={participant.name}
    >
      {initials}
    </span>
  );
}

export function AvatarStack({ participants }: { participants: Participant[] }) {
  const visible = participants.slice(0, 3);
  return (
    <div className="avatar-stack" aria-label={participants.map((participant) => participant.name).join(", ")}>
      {visible.map((participant) => (
        <Avatar key={participant.id} participant={participant} size="sm" />
      ))}
      {participants.length > 3 && <span className="avatar avatar-sm avatar-more">+{participants.length - 3}</span>}
    </div>
  );
}
