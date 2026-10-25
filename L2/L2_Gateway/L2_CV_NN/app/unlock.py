import time


class Unlocker:
    def __init__(self, allowed, action, min_score=0.45, cooldown=10.0):
        self.allowed = set(allowed)  # jména, která smí odemknout
        self.action = action  # callback: action(name)
        self.min_score = min_score  # přísnější než 0.363 pro zobrazení jména
        self.cooldown = cooldown
        self.last_unlock = 0.0

    def update(self, labels, horns_flags):
        now = time.monotonic()
        if now - self.last_unlock < self.cooldown:
            return None

        for i, (name, score) in enumerate(labels):
            if (
                name in self.allowed
                and score >= self.min_score
                and i < len(horns_flags)
                and horns_flags[i]
            ):
                self.last_unlock = now
                self.action(name)
                return name
        return None
