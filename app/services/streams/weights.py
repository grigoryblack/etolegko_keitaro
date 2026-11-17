from app.models import Stream


def recalc_shares(stream: Stream) -> None:
    """Redistribute shares among active offers, keeping pinned ones fixed.

    Active pinned offers keep their share; the remaining percentage is split
    evenly between active unpinned offers. Removed offers get 0.
    """
    active = [o for o in stream.offers if o.status == "active"]
    pinned_sum = sum(o.share for o in active if o.pinned)
    free = [o for o in active if not o.pinned]
    for o in stream.offers:
        if o.status == "removed":
            o.share = 0
    if free:
        total = max(0, 100 - pinned_sum)
        base = total // len(free)
        remainder = total - base * len(free)
        for i, o in enumerate(free):
            o.share = base + (1 if i < remainder else 0)
