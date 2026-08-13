import json
import re
from dataclasses import dataclass

SPEAKER_LINE = re.compile(r"^(?P<speaker>[A-Za-z][A-Za-z .'-]{0,60}):\s*(?P<text>.+)$")
VTT_TIMESTAMP = re.compile(
    r"(?P<start_h>\d{2}):(?P<start_m>\d{2}):(?P<start_s>\d{2})[.,](?P<start_ms>\d{3})"
    r"\s+-->\s+"
    r"(?P<end_h>\d{2}):(?P<end_m>\d{2}):(?P<end_s>\d{2})[.,](?P<end_ms>\d{3})"
)


@dataclass(frozen=True)
class ParsedSegment:
    speaker_name: str
    text: str
    start_in_seconds: float
    end_in_seconds: float


def _seconds(match: re.Match[str], prefix: str) -> float:
    return (
        int(match[f"{prefix}_h"]) * 3600
        + int(match[f"{prefix}_m"]) * 60
        + int(match[f"{prefix}_s"])
        + int(match[f"{prefix}_ms"]) / 1000
    )


def parse_vtt(content: str, fallback_speaker: str) -> list[ParsedSegment]:
    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n").strip())
    segments: list[ParsedSegment] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timestamp_index = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if timestamp_index is None:
            continue
        match = VTT_TIMESTAMP.search(lines[timestamp_index])
        if not match:
            continue
        body = " ".join(lines[timestamp_index + 1 :]).strip()
        if not body:
            continue
        speaker_match = SPEAKER_LINE.match(body)
        speaker = speaker_match["speaker"] if speaker_match else fallback_speaker
        text = speaker_match["text"] if speaker_match else body
        segments.append(
            ParsedSegment(
                speaker_name=speaker,
                text=text,
                start_in_seconds=_seconds(match, "start"),
                end_in_seconds=_seconds(match, "end"),
            )
        )
    return segments


def parse_plain_text(content: str, participant_names: list[str]) -> list[ParsedSegment]:
    lines = [line.strip() for line in content.replace("\r\n", "\n").splitlines() if line.strip()]
    if len(lines) == 1:
        lines = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", lines[0]) if sentence]

    segments: list[ParsedSegment] = []
    cursor = 0.0
    for index, line in enumerate(lines):
        match = SPEAKER_LINE.match(line)
        speaker = match["speaker"] if match else participant_names[index % len(participant_names)]
        text = match["text"] if match else line
        duration = max(3.5, min(28.0, len(text.split()) * 0.42))
        segments.append(
            ParsedSegment(
                speaker_name=speaker,
                text=text,
                start_in_seconds=round(cursor, 2),
                end_in_seconds=round(cursor + duration, 2),
            )
        )
        cursor += duration + 0.35
    return segments


def parse_json(content: str, fallback_speaker: str) -> list[ParsedSegment]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("The JSON transcript is not valid JSON") from error
    rows = payload.get("segments") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("JSON transcript must be an array or contain a segments array")
    segments: list[ParsedSegment] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not str(row.get("text", "")).strip():
            raise ValueError(f"Transcript segment {index + 1} is missing text")
        start = float(row.get("startInSeconds", row.get("start", index * 5)))
        end = float(row.get("endInSeconds", row.get("end", start + 5)))
        if start < 0 or end < start:
            raise ValueError(f"Transcript segment {index + 1} has invalid timestamps")
        segments.append(
            ParsedSegment(
                speaker_name=str(row.get("speaker", fallback_speaker)).strip() or fallback_speaker,
                text=str(row["text"]).strip(),
                start_in_seconds=start,
                end_in_seconds=end,
            )
        )
    return segments


def parse_transcript(
    content: str, participant_names: list[str], file_type: str = "txt"
) -> list[ParsedSegment]:
    fallback = participant_names[0]
    normalized_type = file_type.lower().lstrip(".")
    if normalized_type == "vtt":
        parsed = parse_vtt(content, fallback)
    elif normalized_type == "json":
        parsed = parse_json(content, fallback)
    else:
        parsed = parse_plain_text(content, participant_names)
    if not parsed:
        raise ValueError("The transcript does not contain any readable dialogue")
    return parsed


def build_summary(segments: list[ParsedSegment]) -> tuple[str, list[str]]:
    substantive = [segment.text.strip() for segment in segments if len(segment.text.split()) >= 5]
    selected = substantive[:3] or [segment.text.strip() for segment in segments[:3]]
    overview = " ".join(selected)
    if len(overview) > 420:
        overview = f"{overview[:417].rstrip()}..."
    return overview, selected[:3]
