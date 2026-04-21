def normalize_pagination(
    page: int, limit: int, *, max_limit: int = 100
) -> tuple[int, int, int]:
    """Return ``(page, limit, offset)`` with sane bounds (no I/O)."""
    safe_page = max(page, 1)
    safe_limit = min(max(limit, 1), max_limit)
    offset = (safe_page - 1) * safe_limit
    return safe_page, safe_limit, offset
