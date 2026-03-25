"""Data model for single-story infographic content."""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict


@dataclass
class StoryContent:
    """Everything needed to render a single-story infographic and post it."""
    hook: str
    headline: str
    body: list[str]
    insight: str
    source: str
    source_url: str
    pillar: str
    account: str
    hashtags: list[str] = field(default_factory=list)
    caption: str = ""
    strategy: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> StoryContent:
        return cls(**data)

    def to_json(self, path: str) -> None:
        from pathlib import Path
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def from_json(cls, path: str) -> StoryContent:
        from pathlib import Path
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)
