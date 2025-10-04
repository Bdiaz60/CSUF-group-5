from typing import List

BLOCKLIST = {
    "hate": ["slur1", "slur2"],
    "self-harm": ["suicide", "hurtmyself"],
    "violence": ["kill", "stab", "shoot"]
}

def flag_post(text: str) -> dict:
    """Return whether the post needs review."""
    words = text.lower().split()
    reasons: List[str] = []

    for label, banned in BLOCKLIST.items():
        if any(w in words for w in banned):
            reasons.append(label)

    return {
        "flagged": bool(reasons),
        "reasons": reasons,
        "action": "send_to_human_reviewer" if reasons else "publish"
    }

if __name__ == "__main__":
    sample = "I love sports but want to shoot a scene in the park"
    print(flag_post(sample))
