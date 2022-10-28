class Day:
    def __init__(self, date):
        self.date = date
        self.target_time = 0
        self.actual_time = 0
        self.time_entries = 0
        self.exceptions = set()

    def fullfillment_rate(self) -> float:
        return self.actual_time / self.target_time if self.target_time != 0 else None

    def delta(self):
        return self.actual_time - self.target_time

    def __repr__(self):
        return f"<Day(target_time={self.target_time};actual_time={self.actual_time})>"


class Week:
    def __init__(self, year: int, week: int):
        self.days = set()
        self.year = year
        self.week = week

    def target_time(self) -> int:
        return sum(map(lambda x: x.target_time, self.days))

    def actual_time(self) -> int:
        return sum(map(lambda x: x.actual_time, self.days))

    def fullfillment_rate(self) -> float:
        return (
            self.actual_time() / self.target_time() if self.target_time() != 0 else None
        )

    def delta(self) -> int:
        return self.actual_time() - self.target_time()
