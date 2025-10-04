from typing import List, Dict
import math

def distribution(items: List[str]) -> Dict[str, float]:
    total = max(1, len(items))
    counts: Dict[str, float] = {}
    for x in items:
        counts[x] = counts.get(x, 0) + 1
    return {k: v / total for k, v in counts.items()}

def kl_divergence(p: Dict[str, float], q: Dict[str, float]) -> float:
    """Simple KL divergence to measure distribution difference."""
    eps = 1e-9
    all_keys = set(p) | set(q)
    s = 0.0
    for k in all_keys:
        pk = p.get(k, 0) + eps
        qk = q.get(k, 0) + eps
        s += pk * math.log(pk / qk)
    return s

def check_feed(categories: List[str], target: Dict[str, float], threshold: float = 0.2) -> Dict:
    dist = distribution(categories)
    kl = kl_divergence(dist, target)
    return {
        "distribution": dist,
        "target": target,
        "kl_divergence": round(kl, 3),
        "requires_review": kl > threshold
    }

if __name__ == "__main__":
    feed = ["sports", "tech", "sports", "food", "sports", "fashion"]
    target = {"sports":0.25,"tech":0.25,"food":0.25,"fashion":0.25}
    print(check_feed(feed, target))
