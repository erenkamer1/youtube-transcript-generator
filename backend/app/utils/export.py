from app.schemas import SegmentSchema


def _format_timestamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _format_vtt_timestamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"


def export_txt(segments: list[SegmentSchema]) -> str:
    return "\n".join(segment.text for segment in segments)


def export_srt(segments: list[SegmentSchema]) -> str:
    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        lines.extend(
            [
                str(index),
                f"{_format_timestamp(segment.start)} --> {_format_timestamp(segment.end)}",
                segment.text,
                "",
            ]
        )
    return "\n".join(lines)


def export_vtt(segments: list[SegmentSchema]) -> str:
    lines = ["WEBVTT", ""]
    for segment in segments:
        lines.extend(
            [
                f"{_format_vtt_timestamp(segment.start)} --> {_format_vtt_timestamp(segment.end)}",
                segment.text,
                "",
            ]
        )
    return "\n".join(lines)
