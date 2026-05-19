from __future__ import annotations

import re
from typing import Any

from .base import cell_text, upsert_record


TARGET_TABLE_BY_RELATED_FIELD = {
    "Related Task": "Tasks",
    "Related Tasks": "Tasks",
    "Related Bugfix": "Bugfixes",
    "Related Bugfixes": "Bugfixes",
    "Related Pitfall": "Pitfalls",
    "Related Pitfalls": "Pitfalls",
    "Related Playbook": "Playbooks",
    "Related Playbooks": "Playbooks",
    "Related Decision": "Decisions",
    "Related Decisions": "Decisions",
    "Related Release": "Releases",
    "Related Releases": "Releases",
    "Related Artifact": "Artifacts",
    "Related Artifacts": "Artifacts",
    "Related AI Run": "AI Runs",
    "Related AI Runs": "AI Runs",
    "Related Project Fact": "Project Facts",
    "Related Project Facts": "Project Facts",
}


def split_relation_refs(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(split_relation_refs(item))
        return refs
    if isinstance(value, dict):
        for key in ("id", "record_id", "title", "text", "name", "value"):
            if value.get(key):
                return [str(value[key])]
        return []
    refs: list[str] = []
    for part in re.split(r"[\n,，;；]+", str(value)):
        cleaned = part.strip().strip("`'\"[]()")
        if cleaned:
            refs.append(cleaned)
    return refs


def infer_target_table(field: str, ref: str) -> tuple[str, str]:
    if field in TARGET_TABLE_BY_RELATED_FIELD:
        return TARGET_TABLE_BY_RELATED_FIELD[field], ref
    if field == "Related Records" and ":" in ref:
        table, target = ref.split(":", 1)
        table = table.strip()
        target = target.strip()
        if table in set(TARGET_TABLE_BY_RELATED_FIELD.values()) | {"Projects", "Areas"}:
            return table, target
    return "", ref


def relation_type_for(source_table: str, target_table: str) -> str:
    if source_table == "Bugfixes" and target_table == "Tasks":
        return "fixes"
    if source_table == "AI Runs":
        return "evidence_for"
    if source_table == "Artifacts":
        return "documents"
    if source_table == "Decisions":
        return "decided_by"
    if source_table == "Releases":
        return "verifies"
    return "relates_to"


def build_relation_payloads(source_table: str, source_record_id: str, source_payload: dict[str, Any]) -> list[dict[str, Any]]:
    if source_table == "Record Relations":
        return []
    source_title = cell_text(source_payload.get("Title")).strip()
    project = cell_text(source_payload.get("Project")).strip()
    area = cell_text(source_payload.get("Area")).strip()
    evidence = cell_text(source_payload.get("Evidence") or source_payload.get("AI Summary")).strip()
    payloads: list[dict[str, Any]] = []
    for field, value in source_payload.items():
        if not field.startswith("Related "):
            continue
        for raw_ref in split_relation_refs(value):
            target_table, target_ref = infer_target_table(field, raw_ref)
            target_record_id = target_ref if target_ref.startswith("rec") else ""
            title_target = target_record_id or target_ref
            title = f"{source_table}:{source_title} -> {target_table or 'Unknown'}:{title_target}"
            keywords = " ".join(
                part
                for part in [
                    project,
                    area,
                    source_table,
                    source_title,
                    target_table,
                    target_ref,
                    relation_type_for(source_table, target_table),
                ]
                if part
            )
            payloads.append(
                {
                    "Title": title,
                    "Project": project,
                    "Area": area,
                    "Status": "Active",
                    "Relation Type": relation_type_for(source_table, target_table),
                    "Source Table": source_table,
                    "Source Record ID": source_record_id,
                    "Source Title": source_title,
                    "Target Table": target_table,
                    "Target Record ID": target_record_id,
                    "Target Ref": target_ref,
                    "Evidence": evidence,
                    "AI Summary": f"{source_table} record links to {target_table or 'a referenced record'}: {target_ref}",
                    "Search Keywords": keywords,
                    "Source URL": source_payload.get("Source URL", ""),
                }
            )
    return payloads


def write_record_relations(config: dict[str, Any], source_table: str, source_record_id: str, source_payload: dict[str, Any]) -> list[str]:
    if "Record Relations" not in config.get("base", {}).get("tables", {}):
        return []
    record_ids: list[str] = []
    for payload in build_relation_payloads(source_table, source_record_id, source_payload):
        output, _ = upsert_record(
            config,
            "Record Relations",
            payload,
            match_fields=["Source Table", "Source Record ID", "Relation Type", "Target Table", "Target Ref"],
        )
        record_id = cell_text(output.get("_record_id") or output.get("record_id") or output.get("record_url") or output.get("url"))
        if record_id:
            record_ids.append(record_id)
    return record_ids
