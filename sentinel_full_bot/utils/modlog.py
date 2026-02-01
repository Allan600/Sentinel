from datetime import datetime
from collections import defaultdict

# user_id -> list of actions
USER_HISTORY = defaultdict(list)


def log_action(
    *,
    action: str,
    target_id: int,
    moderator: str,
    reason: str | None = None,
    extra: dict | None = None
):
    USER_HISTORY[target_id].append({
        "action": action,
        "moderator": moderator,
        "reason": reason or "No reason provided",
        "extra": extra or {},
        "timestamp": datetime.utcnow()
    })


def get_history(user_id: int):
    return USER_HISTORY.get(user_id, [])
