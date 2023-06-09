from __future__ import annotations

import typing
from typing import Sequence, Iterator
from datetime import datetime, timedelta


class TimeBlockInterface(typing.Protocol):
    time_start: datetime
    time_end: datetime
    name: str
    hover_text: str


class TimeBlock:
    counter = 0

    def __init__(self, time_start: datetime, time_end: datetime = None, name: str = None, hover_text: str = None):
        self.time_start = time_start
        self.time_end = time_end
        self.name = name if name is None else f"time_block_{self.counter}"
        self.hover_text = hover_text

        TimeBlock.counter += 1

    def __lt__(self, other: TimeBlock):
        return self.time_start < other.time_start

    def __eq__(self, other):
        return self.time_start == other.time_start


class Row:
    def __init__(self, name: str, time_blocks: list[TimeBlockInterface]):
        self.name = name
        self.time_blocks = time_blocks  # sorted by time

    def __len__(self) -> int:
        return len(self.time_blocks)

    @property
    def time_block_names(self) -> list[str]:
        return [time_block.name for time_block in self.time_blocks]

    def add_time_block(self, time_block: TimeBlockInterface):
        self.time_blocks.append(time_block)
        self.time_blocks.sort()


class GanttChart:
    def __init__(self, rows: list[Row] = None, current_time: datetime = None):
        self._rows = []
        if rows is not None:
            self.add_row(rows)
        self.current_time = current_time

        self._time_min = None
        self._time_max = None
        self._row_labels = []

        self._up_to_date = False

    def __iter__(self):
        return iter(self._rows)

    @property
    def rows(self) -> list[Row]:
        return self._rows

    @property
    def number_of_rows(self) -> int:
        return len(self._rows)

    @property
    def row_labels(self) -> list[str]:
        if not self._up_to_date:
            self._update()
        return self._row_labels

    @property
    def time_min(self) -> datetime | None:
        if not self._up_to_date:
            self._update()
        return self._time_min

    @property
    def time_max(self) -> datetime | None:
        if not self._up_to_date:
            self._update()
        return self._time_max

    @property
    def time_range(self) -> timedelta:
        return self.time_max - self.time_min

    def _update(self):
        self._time_min, self._time_max = get_min_max_time(self.rows)
        self._row_labels = [row.name for row in self.rows]
        self._up_to_date = True

    def add_row(self, row: Row | Iterator[Row]):
        self._up_to_date = False
        if isinstance(row, Row):
            row = [row]
        self._rows += row

    def get_row(self, row: str) -> Row:
        index = self.row_labels.index(row)
        return self._rows[index]

    def add_time_block(self, row: str, time_block: TimeBlockInterface):
        if row not in self.row_labels:
            self.add_row(Row(row, []))

        row = self.get_row(row)
        row.add_time_block(time_block)

        self._up_to_date = False

    def delete_row(self, row: Row | Iterator[Row] | int):
        self._up_to_date = False

        if isinstance(row, int):
            del self._rows[row]
        elif isinstance(row, Row):
            self._rows.remove(row)
        elif isinstance(row, Iterator):
            for row_ in row:
                self._rows.remove(row_)
        else:
            raise ValueError("Invalid argument provided.")


def get_min_max_time(data: Sequence[Row]) -> tuple[datetime | None, datetime | None]:
    if len(data) == 0 or len(data[0].time_blocks) == 0:
        return None, None

    min_time = data[0].time_blocks[0].time_start
    max_time = min_time
    for row in data:
        for time_block in row.time_blocks:
            if time_block.time_start < min_time:
                min_time = time_block.time_start
                continue
            if time_block.time_end is not None and time_block.time_end > max_time:
                max_time = time_block.time_end

    return min_time, max_time


def get_time_delta_label(time_delta: timedelta) -> str:
    if time_delta >= timedelta(days=1):
        return f"{time_delta.days} d"
    if time_delta >= timedelta(hours=1):
        return f"{int(time_delta.seconds / 60 / 60)} h"
    if time_delta >= timedelta(minutes=1):
        return f"{int(time_delta.seconds / 60)} min"
    if time_delta >= timedelta(seconds=1):
        return f"{time_delta.seconds} s"
    return f"{time_delta.microseconds} ms"
