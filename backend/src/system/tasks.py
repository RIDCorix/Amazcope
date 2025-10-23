import dramatiq


@dramatiq.actor(store_results=True)
def simple_add(x: int, y: int) -> int:
    """A simple test task."""
    return x + y
