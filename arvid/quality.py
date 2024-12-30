from dataclasses import dataclass


type Quality = Min | Max | Exact | Closest


class Min:
    pass


class Max:
    pass


@dataclass
class Exact:
    val: int


@dataclass
class Closest:
    val: int


def get_quality(opts: list[int], q: Quality) -> int:
    match q:
        case Min() if opts:
            return min(opts)
        case Max() if opts:
            return max(opts)
        case Exact(val) if val in opts:
            return val
        case Closest(val) if opts:
            return min((abs(o - val), o) for o in opts)[1]
        case _:
            raise ValueError
