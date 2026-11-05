"""Keep repository links readable on GitHub and valid in the built handbook."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
from urllib.parse import quote, unquote


def on_config(config):
    root = Path(config.config_file_path).resolve().parent
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = "main"
    config.extra["source_revision"] = revision
    return config


def on_page_markdown(markdown, *, page, config, files):
    root = Path(config.config_file_path).resolve().parent
    docs = Path(config.docs_dir).resolve()
    source = Path(page.file.abs_src_path)
    revision = config.extra["source_revision"]
    repository = config.repo_url.rstrip("/")

    def replace(match):
        prefix, raw, suffix = match.groups()
        if raw.startswith(("#", "http:", "https:", "mailto:")):
            return match.group(0)
        path_text, sep, fragment = raw.partition("#")
        target = (source.parent / unquote(path_text)).resolve()
        if target.is_relative_to(docs):
            return match.group(0)
        if not target.is_relative_to(root) or not target.exists():
            raise ValueError(f"{page.file.src_path}: invalid repository link {raw}")
        relative = target.relative_to(root).as_posix()
        url = repository + "/blob/" + revision + "/" + quote(relative, safe="/")
        return prefix + url + (sep + fragment if sep else "") + suffix

    # The handbook uses ordinary relative Markdown links. File existence is
    # checked here; its dedicated checker also checks local Markdown fragments.
    return re.sub(r"(!?\[[^\]]*\]\()([^\s)]+)(\))", replace, markdown)
