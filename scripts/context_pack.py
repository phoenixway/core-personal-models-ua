#!/usr/bin/env python3

from __future__ import annotations

import argparse
import fnmatch
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
import tomllib


DEFAULT_CONFIG_PATH = Path("config/context-pack.toml")


@dataclass(frozen=True)
class FileEntry:
    relative_path: str
    absolute_path: Path
    content: str
    char_count: int
    token_estimate: int


@dataclass(frozen=True)
class Config:
    output_dir: Path
    strategy: str
    max_chars_per_pack: int
    max_output_files: int | None
    subdir_pack_threshold: int
    include_extensions: tuple[str, ...]
    include_globs: tuple[str, ...]
    exclude_globs: tuple[str, ...]
    exclude_dirs: tuple[str, ...]
    include_files: tuple[str, ...]
    exclude_files: tuple[str, ...]
    include_root_files: bool
    tree_header: bool


def require_table(data: dict, key: str, config_path: Path) -> dict:
    value = data.get(key)
    if not isinstance(value, dict):
        raise SystemExit(f"Config {config_path} must contain a [{key}] table.")
    return value


def require_list(table: dict, key: str, config_path: Path, table_name: str) -> tuple[str, ...]:
    value = table.get(key)
    if not isinstance(value, list):
        raise SystemExit(f"Config {config_path} must contain a {table_name}.{key} list.")
    return tuple(str(item) for item in value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pack markdown files from a target folder into model-friendly bundles."
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Target folder to pack, relative to the repository root or absolute.",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help=f"Path to TOML config file. Defaults to {DEFAULT_CONFIG_PATH}.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional override for the output directory from config.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files and packs would be generated without writing files.",
    )
    return parser.parse_args()


def load_config(config_path: Path) -> Config:
    if not config_path.is_file():
        raise SystemExit(f"Config not found: {config_path}")

    with config_path.open("rb") as handle:
        data = tomllib.load(handle)

    try:
        output = require_table(data, "output", config_path)
        packing = require_table(data, "packing", config_path)
        include = require_table(data, "include", config_path)
        exclude = require_table(data, "exclude", config_path)
        render = require_table(data, "render", config_path)

        output_dir = Path(output["dir"])
        strategy = str(packing["strategy"])
        max_chars_per_pack = int(packing["max_chars_per_pack"])
        max_output_files_value = packing.get("max_output_files")
        subdir_pack_threshold = int(packing["subdir_pack_threshold"])
        include_extensions = require_list(include, "extensions", config_path, "include")
        include_globs = require_list(include, "globs", config_path, "include")
        include_files = require_list(include, "files", config_path, "include")
        include_root_files = bool(include["root_files"])
        exclude_globs = require_list(exclude, "globs", config_path, "exclude")
        exclude_dirs = require_list(exclude, "dirs", config_path, "exclude")
        exclude_files = require_list(exclude, "files", config_path, "exclude")
        tree_header = bool(render["tree_header"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"Invalid config format in {config_path}: {exc}") from exc

    valid_strategies = {"by-size", "by-subdir", "hybrid"}
    if strategy not in valid_strategies:
        raise SystemExit(f"Unsupported strategy '{strategy}'. Use one of: {sorted(valid_strategies)}")

    if max_chars_per_pack <= 0:
        raise SystemExit("max_chars_per_pack must be greater than zero.")

    if max_output_files_value is None:
        max_output_files = None
    else:
        max_output_files = int(max_output_files_value)
        if max_output_files < 2:
            raise SystemExit("packing.max_output_files must be at least 2 because manifest.md is always generated.")

    if subdir_pack_threshold < 0:
        raise SystemExit("subdir_pack_threshold must be zero or greater.")

    return Config(
        output_dir=output_dir,
        strategy=strategy,
        max_chars_per_pack=max_chars_per_pack,
        max_output_files=max_output_files,
        subdir_pack_threshold=subdir_pack_threshold,
        include_extensions=include_extensions,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        exclude_dirs=exclude_dirs,
        include_files=include_files,
        exclude_files=exclude_files,
        include_root_files=include_root_files,
        tree_header=tree_header,
    )


def resolve_root(root_arg: str, workspace_root: Path) -> Path:
    candidate = Path(root_arg)
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    candidate = candidate.resolve()

    try:
        candidate.relative_to(workspace_root)
    except ValueError as exc:
        raise SystemExit("The target root must stay inside the repository.") from exc

    if not candidate.is_dir():
        raise SystemExit(f"Target root is not a directory: {candidate}")
    return candidate


def normalize(path: str) -> str:
    return path.replace("\\", "/")


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def should_exclude_dir(relative_dir: str, relative_to_workspace: str, config: Config) -> bool:
    parts = Path(relative_dir).parts
    if any(part in config.exclude_dirs for part in parts):
        return True
    normalized_patterns = {normalize(item).strip("/") for item in config.exclude_dirs}
    if relative_dir in normalized_patterns:
        return True
    if relative_to_workspace in normalized_patterns:
        return True
    if any(relative_dir.startswith(f"{pattern}/") for pattern in normalized_patterns if pattern):
        return True
    if any(relative_to_workspace.startswith(f"{pattern}/") for pattern in normalized_patterns if pattern):
        return True
    return matches_any(relative_dir, config.exclude_globs) or matches_any(
        relative_to_workspace, config.exclude_globs
    )


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def make_slug(path_text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", path_text.strip("/"))
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "root"


def collect_files(root_dir: Path, workspace_root: Path, config: Config) -> tuple[list[FileEntry], list[str]]:
    included: list[FileEntry] = []
    excluded: list[str] = []

    for current_dir, dirnames, filenames in root_dir.walk(top_down=True):
        current_path = Path(current_dir)
        relative_dir = normalize(str(current_path.relative_to(root_dir)))
        if relative_dir == ".":
            relative_dir = ""

        kept_dirnames: list[str] = []
        for dirname in sorted(dirnames):
            relative_child = normalize(f"{relative_dir}/{dirname}".strip("/"))
            workspace_child = normalize(str((current_path / dirname).relative_to(workspace_root)))
            if should_exclude_dir(relative_child, workspace_child, config):
                excluded.append(f"{workspace_child}/  [excluded-dir]")
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        for filename in sorted(filenames):
            file_path = current_path / filename
            relative_to_root = normalize(str(file_path.relative_to(root_dir)))
            relative_to_workspace = normalize(str(file_path.relative_to(workspace_root)))

            if not config.include_root_files and "/" not in relative_to_root:
                excluded.append(f"{relative_to_workspace}  [root-files-disabled]")
                continue

            if file_path.suffix not in config.include_extensions:
                excluded.append(f"{relative_to_workspace}  [extension]")
                continue

            if matches_any(relative_to_root, config.exclude_files) or matches_any(
                relative_to_workspace, config.exclude_files
            ):
                excluded.append(f"{relative_to_workspace}  [exclude-files]")
                continue

            if config.include_files and not (
                matches_any(relative_to_root, config.include_files)
                or matches_any(relative_to_workspace, config.include_files)
            ):
                include_match = matches_any(relative_to_root, config.include_globs) or matches_any(
                    relative_to_workspace, config.include_globs
                )
                if not include_match:
                    excluded.append(f"{relative_to_workspace}  [not-in-include]")
                    continue
            else:
                include_match = matches_any(relative_to_root, config.include_globs) or matches_any(
                    relative_to_workspace, config.include_globs
                )
                forced_include = (
                    matches_any(relative_to_root, config.include_files)
                    or matches_any(relative_to_workspace, config.include_files)
                )
                if not include_match and not forced_include:
                    excluded.append(f"{relative_to_workspace}  [not-in-include]")
                    continue

            if matches_any(relative_to_root, config.exclude_globs) or matches_any(
                relative_to_workspace, config.exclude_globs
            ):
                excluded.append(f"{relative_to_workspace}  [exclude-glob]")
                continue

            content = file_path.read_text(encoding="utf-8")
            included.append(
                FileEntry(
                    relative_path=relative_to_workspace,
                    absolute_path=file_path,
                    content=content,
                    char_count=len(content),
                    token_estimate=estimate_tokens(content),
                )
            )

    included.sort(key=lambda entry: entry.relative_path)
    excluded.sort()
    return included, excluded


def split_by_immediate_group(entries: list[FileEntry], root_dir: Path, workspace_root: Path) -> tuple[list[FileEntry], dict[str, list[FileEntry]]]:
    root_files: list[FileEntry] = []
    grouped: dict[str, list[FileEntry]] = {}
    root_prefix = normalize(str(root_dir.relative_to(workspace_root)))

    for entry in entries:
        relative_to_root = entry.relative_path[len(root_prefix) :].lstrip("/")
        if "/" not in relative_to_root:
            root_files.append(entry)
            continue
        group = relative_to_root.split("/", 1)[0]
        grouped.setdefault(group, []).append(entry)

    return root_files, dict(sorted(grouped.items()))


def build_file_block(entry: FileEntry) -> str:
    return (
        "===== FILE START =====\n"
        f"path: {entry.relative_path}\n"
        f"chars: {entry.char_count}\n"
        f"tokens_estimate: {entry.token_estimate}\n"
        "===== CONTENT =====\n"
        f"{entry.content.rstrip()}\n\n"
    )


def chunk_entries(entries: list[FileEntry], max_chars: int) -> list[list[FileEntry]]:
    if not entries:
        return []

    chunks: list[list[FileEntry]] = []
    current_chunk: list[FileEntry] = []
    current_size = 0

    for entry in entries:
        block_size = len(build_file_block(entry))
        if current_chunk and current_size + block_size > max_chars:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0
        current_chunk.append(entry)
        current_size += block_size
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def render_tree(entries: list[FileEntry]) -> str:
    lines = ["Included files:"]
    for entry in entries:
        lines.append(f"- {entry.relative_path}")
    return "\n".join(lines)


def render_pack(root_label: str, pack_name: str, entries: list[FileEntry], config: Config) -> str:
    header_lines = [
        f"# Context Pack: {pack_name}",
        "",
        f"- root: {root_label}",
        f"- files: {len(entries)}",
        f"- total_chars: {sum(entry.char_count for entry in entries)}",
        f"- total_tokens_estimate: {sum(entry.token_estimate for entry in entries)}",
        "",
    ]

    if config.tree_header:
        header_lines.extend([render_tree(entries), ""])

    body = "".join(build_file_block(entry) for entry in entries)
    return "\n".join(header_lines) + body


def plan_packs(entries: list[FileEntry], root_dir: Path, workspace_root: Path, config: Config) -> list[tuple[str, list[FileEntry]]]:
    root_label = normalize(str(root_dir.relative_to(workspace_root)))
    root_files, grouped = split_by_immediate_group(entries, root_dir, workspace_root)
    immediate_subdir_count = len(grouped)

    use_subdir_strategy = config.strategy == "by-subdir" or (
        config.strategy == "hybrid" and 0 < immediate_subdir_count <= config.subdir_pack_threshold
    )

    planned: list[tuple[str, list[FileEntry]]] = []
    if use_subdir_strategy:
        if root_files:
            planned.extend(
                (f"{make_slug(root_label)}-root-part-{index:02d}", chunk)
                for index, chunk in enumerate(chunk_entries(root_files, config.max_chars_per_pack), start=1)
            )
        for group_name, group_entries in grouped.items():
            base_name = f"{make_slug(root_label)}-{make_slug(group_name)}"
            planned.extend(
                (f"{base_name}-part-{index:02d}", chunk)
                for index, chunk in enumerate(chunk_entries(group_entries, config.max_chars_per_pack), start=1)
            )
        return planned

    all_chunks = chunk_entries(entries, config.max_chars_per_pack)
    return [
        (f"{make_slug(root_label)}-part-{index:02d}", chunk)
        for index, chunk in enumerate(all_chunks, start=1)
    ]


def enforce_max_output_files(
    packs: list[tuple[str, list[FileEntry]]],
    root_dir: Path,
    workspace_root: Path,
    config: Config,
) -> list[tuple[str, list[FileEntry]]]:
    if config.max_output_files is None:
        return packs

    max_pack_files = config.max_output_files - 1
    if max_pack_files < 1:
        raise SystemExit("packing.max_output_files leaves no room for content packs.")

    if len(packs) <= max_pack_files:
        return packs

    root_label = normalize(str(root_dir.relative_to(workspace_root)))
    merged_entries: list[FileEntry] = []
    for _, entries in packs:
        merged_entries.extend(entries)

    merged_entries.sort(key=lambda entry: entry.relative_path)
    chunk_size = max(1, math.ceil(len(merged_entries) / max_pack_files))
    merged_packs: list[tuple[str, list[FileEntry]]] = []
    for index in range(max_pack_files):
        start = index * chunk_size
        end = start + chunk_size
        chunk = merged_entries[start:end]
        if not chunk:
            continue
        merged_packs.append((f"{make_slug(root_label)}-part-{index + 1:02d}", chunk))

    return merged_packs


def build_manifest(
    root_label: str,
    output_dir: Path,
    packs: list[tuple[str, list[FileEntry]]],
    excluded: list[str],
) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Context Pack Manifest",
        "",
        f"- root: {root_label}",
        f"- output_dir: {output_dir}",
        f"- generated_at_utc: {generated_at}",
        f"- pack_count: {len(packs)}",
        "",
        "## Packs",
        "",
    ]

    for pack_name, entries in packs:
        lines.append(
            f"- {pack_name}.md: files={len(entries)}, chars={sum(entry.char_count for entry in entries)}, tokens_estimate={sum(entry.token_estimate for entry in entries)}"
        )
        for entry in entries:
            lines.append(f"  - {entry.relative_path}")

    lines.extend(["", "## Excluded", ""])
    if excluded:
        lines.extend(f"- {item}" for item in excluded)
    else:
        lines.append("- None")

    lines.append("")
    return "\n".join(lines)


def write_outputs(output_dir: Path, root_label: str, packs: list[tuple[str, list[FileEntry]]], excluded: list[str], config: Config) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for existing_file in output_dir.glob("*.md"):
        existing_file.unlink()

    for pack_name, entries in packs:
        content = render_pack(root_label, pack_name, entries, config)
        (output_dir / f"{pack_name}.md").write_text(content, encoding="utf-8")

    manifest = build_manifest(root_label, output_dir, packs, excluded)
    (output_dir / "manifest.md").write_text(manifest, encoding="utf-8")


def print_dry_run(root_label: str, output_dir: Path, packs: list[tuple[str, list[FileEntry]]], excluded: list[str]) -> None:
    print(f"root: {root_label}")
    print(f"output_dir: {output_dir}")
    print(f"pack_count: {len(packs)}")
    print("")
    for pack_name, entries in packs:
        print(
            f"{pack_name}.md | files={len(entries)} | chars={sum(entry.char_count for entry in entries)} | tokens~={sum(entry.token_estimate for entry in entries)}"
        )
        for entry in entries:
            print(f"  - {entry.relative_path}")
    print("")
    print(f"excluded_count: {len(excluded)}")
    for item in excluded[:50]:
        print(f"  - {item}")
    if len(excluded) > 50:
        print(f"  ... and {len(excluded) - 50} more")


def main() -> int:
    args = parse_args()
    workspace_root = Path.cwd().resolve()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = workspace_root / config_path
    config = load_config(config_path)

    if args.output_dir:
        config = Config(**{**config.__dict__, "output_dir": Path(args.output_dir)})

    root_dir = resolve_root(args.root, workspace_root)
    root_label = normalize(str(root_dir.relative_to(workspace_root)))
    entries, excluded = collect_files(root_dir, workspace_root, config)
    packs = plan_packs(entries, root_dir, workspace_root, config)
    packs = enforce_max_output_files(packs, root_dir, workspace_root, config)

    if not packs:
        raise SystemExit("No files matched the current config.")

    output_dir = config.output_dir / make_slug(root_label)

    if args.dry_run:
        print_dry_run(root_label, output_dir, packs, excluded)
        return 0

    write_outputs(output_dir, root_label, packs, excluded, config)
    print(f"Wrote {len(packs)} pack(s) and manifest to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
