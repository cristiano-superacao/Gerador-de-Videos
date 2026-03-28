ALLOWED_MEDIA_EXTENSIONS = (
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
)

MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024


def get_allowed_media_extensions() -> list[str]:
    return [extension.lstrip(".") for extension in ALLOWED_MEDIA_EXTENSIONS]


def format_human_list(values: list[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return f"{', '.join(values[:-1])} ou {values[-1]}"


def get_allowed_media_extensions_label() -> str:
    return format_human_list(get_allowed_media_extensions())


def get_max_upload_size_mb() -> int:
    return MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
