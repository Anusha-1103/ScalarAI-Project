import json
import logging
import re
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.common.settings_config import Settings, get_settings
from app.modules.meetings.transcript_helper import ParsedSegment, build_summary

logger = logging.getLogger(__name__)


class AnalysisChapter(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    start_in_seconds: float = Field(ge=0)


class AnalysisAction(BaseModel):
    description: str = Field(min_length=2, max_length=500)
    assignee_name: str | None = Field(default=None, max_length=120)


class TranscriptAnalysis(BaseModel):
    overview: str = Field(min_length=10, max_length=1200)
    key_points: list[str] = Field(min_length=1, max_length=6)
    chapters: list[AnalysisChapter] = Field(min_length=1, max_length=8)
    action_items: list[AnalysisAction] = Field(default_factory=list, max_length=12)


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    used_ai: bool


class MeetingAIService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.groq_api_key)

    @staticmethod
    def _transcript_text(segments: list[ParsedSegment]) -> str:
        return "\n".join(
            f"[{segment.start_in_seconds:.2f}s] {segment.speaker_name}: {segment.text}"
            for segment in segments
        )[:60_000]

    async def _complete(self, *, system: str, user: str, json_mode: bool = False) -> str:
        if not self.settings.groq_api_key:
            raise RuntimeError("Groq is not configured")
        payload: dict[str, object] = {
            "model": self.settings.groq_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "max_completion_tokens": 1400,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=self.settings.groq_timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.groq_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"]).strip()

    @staticmethod
    def _fallback_analysis(segments: list[ParsedSegment]) -> TranscriptAnalysis:
        overview, points = build_summary(segments)
        chapter_indexes = sorted({0, len(segments) // 3, (len(segments) * 2) // 3})
        chapters = [
            AnalysisChapter(
                title=(
                    "Opening and context"
                    if index == 0
                    else f"Discussion: {segments[index].text[:52].rstrip('.')}"
                ),
                start_in_seconds=segments[index].start_in_seconds,
            )
            for index in chapter_indexes
        ]
        actions: list[AnalysisAction] = []
        action_pattern = re.compile(
            r"^(?:i|we)\s+(?:will|can|need to|should)\s+(.+)$|"
            r"^(?:please\s+)?(.+?\s+by\s+(?:today|tomorrow|monday|tuesday|"
            r"wednesday|thursday|friday).*)$",
            re.IGNORECASE,
        )
        for segment in segments:
            match = action_pattern.match(segment.text.strip())
            if not match:
                continue
            description = (match.group(1) or match.group(2) or "").strip().rstrip(".")
            if description and all(
                item.description.lower() != description.lower() for item in actions
            ):
                actions.append(
                    AnalysisAction(
                        description=description[0].upper() + description[1:],
                        assignee_name=segment.speaker_name,
                    )
                )
        return TranscriptAnalysis(
            overview=overview,
            key_points=points,
            chapters=chapters,
            action_items=actions[:8],
        )

    @staticmethod
    def _normalize_analysis_payload(payload: object) -> object:
        if not isinstance(payload, dict):
            return payload
        chapters = payload.get("chapters")
        if isinstance(chapters, list):
            normalized_chapters = []
            for chapter in chapters:
                if not isinstance(chapter, dict):
                    normalized_chapters.append(chapter)
                    continue
                timestamp = chapter.get("start_in_seconds", chapter.get("timestamp", 0))
                if isinstance(timestamp, str):
                    timestamp = timestamp.strip().lower().removesuffix("s")
                normalized_chapters.append(
                    {
                        "title": chapter.get("title") or chapter.get("description"),
                        "start_in_seconds": timestamp,
                    }
                )
            payload = {**payload, "chapters": normalized_chapters}
        return payload

    async def analyze(
        self, segments: list[ParsedSegment], *, use_ai: bool = True
    ) -> TranscriptAnalysis:
        fallback = self._fallback_analysis(segments)
        if not use_ai or not self.enabled:
            return fallback
        try:
            content = await self._complete(
                system=(
                    "You are a precise meeting intelligence analyst. Return valid JSON only with "
                    "overview, key_points, chapters, and action_items. Never invent facts, owners, "
                    "deadlines, or decisions. Chapter timestamps must come from the transcript. "
                    "Every chapter must contain title and start_in_seconds as a number. "
                    "Each action item must contain description and assignee_name (or null)."
                ),
                user=(
                    "Analyze this transcript. Write a concise executive overview, 3-5 key points, "
                    "useful timestamped chapters, and only explicit follow-up actions.\n\n"
                    f"{self._transcript_text(segments)}"
                ),
                json_mode=True,
            )
            payload = self._normalize_analysis_payload(json.loads(content))
            return TranscriptAnalysis.model_validate(payload)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, ValidationError) as error:
            logger.warning("Groq transcript analysis failed; using local fallback: %s", error)
            return fallback

    async def answer(self, question: str, evidence: list[str]) -> AnswerResult:
        if not evidence:
            return AnswerResult(
                answer=(
                    "I could not find supporting evidence in your meeting transcripts. "
                    "Try a specific topic, person, decision, or deadline."
                ),
                used_ai=False,
            )
        fallback = " ".join(evidence[:3])
        if not self.enabled:
            return AnswerResult(answer=fallback, used_ai=False)
        numbered_evidence = "\n".join(
            f"Evidence {index + 1}: {snippet}" for index, snippet in enumerate(evidence[:8])
        )
        try:
            answer = await self._complete(
                system=(
                    "Answer only from the supplied meeting evidence. Be concise and direct. "
                    "If the evidence is insufficient, say so. Do not invent details."
                ),
                user=f"Question: {question}\n\n{numbered_evidence}",
            )
            return AnswerResult(answer=answer, used_ai=True)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            logger.warning("Groq question answering failed; returning source evidence: %s", error)
            return AnswerResult(answer=fallback, used_ai=False)
