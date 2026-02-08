import re


def generate_slug(name: str) -> str:
    """
    Generate a URL-friendly slug from a string.

    Example:
        "Free Plan Example" -> "free-plan-example"
    """
    if not name:
        return ""

    slug = name.lower()  # lowercase
    slug = re.sub(r"[^\w\s-]", "", slug)  # remove special characters
    slug = re.sub(r"\s+", "-", slug)  # replace spaces with dashes
    slug = re.sub(r"-+", "-", slug)  # remove consecutive dashes
    return slug.strip("-")
