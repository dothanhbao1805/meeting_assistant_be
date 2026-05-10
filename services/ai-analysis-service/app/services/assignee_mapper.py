# assignee_mapper.py


def map_assignees(tasks_data: list[dict], participants: list[dict]) -> list[dict]:
    for task in tasks_data:
        raw = (task.get("raw_assignee_text") or "").strip()
        if not raw:
            task["resolved_user_id"] = None
            continue

        # Ưu tiên 1: match speaker_label (Speaker_0, Speaker_1,...)
        for p in participants:
            if p.get("speaker_label") and p["speaker_label"].lower() == raw.lower():
                task["resolved_user_id"] = p["user_id"]
                break
        else:
            # Fallback: match full_name
            raw_lower = raw.lower()
            best_match = None
            best_score = 0

            for p in participants:
                full_name = (p.get("full_name") or "").lower().strip()
                if not full_name:
                    continue

                raw_words = set(raw_lower.split())
                name_words = set(full_name.split())
                score = len(raw_words & name_words)

                if full_name in raw_lower or raw_lower in full_name:
                    score += 2

                if score > best_score:
                    best_score = score
                    best_match = p

            task["resolved_user_id"] = (
                best_match["user_id"] if best_match and best_score > 0 else None
            )

    return tasks_data
