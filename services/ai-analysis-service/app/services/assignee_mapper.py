def map_assignees(tasks_data: list[dict], participants: list[dict]) -> list[dict]:
    """
    So sánh raw_assignee_text với full_name của participants.
    Ưu tiên match nhiều từ nhất.
    """
    for task in tasks_data:
        raw = (task.get("raw_assignee_text") or "").lower().strip()
        if not raw:
            task["resolved_user_id"] = None
            continue

        best_match = None
        best_score = 0

        for p in participants:
            full_name = (p.get("full_name") or "").lower().strip()
            if not full_name:
                continue

            # Tách từ và đếm số từ trùng nhau
            raw_words = set(raw.split())
            name_words = set(full_name.split())
            score = len(raw_words & name_words)

            # Bonus nếu tên chứa trong raw hoặc ngược lại
            if full_name in raw or raw in full_name:
                score += 2

            if score > best_score:
                best_score = score
                best_match = p

        # Chỉ map nếu có ít nhất 1 từ trùng
        task["resolved_user_id"] = best_match["user_id"] if best_match and best_score > 0 else None

    return tasks_data