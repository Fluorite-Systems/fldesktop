from dataclasses import dataclass


@dataclass(slots=True)
class Node: 
    id: int
    attrs: dict