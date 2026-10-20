from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictBool

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class ExtractionInput(Input):
    records: list[dict[str, Any]] = Field(max_length=5000)
    required_fields: list[str] = Field(default_factory=list, max_length=64, description='RFC6901 pointers, e.g. /name')
    unique_fields: list[str] = Field(default_factory=list, max_length=64, description='Composite unique key pointers')
    expected_count: StrictInt = Field(default=None, ge=0, description='Total expected records in the whole supplied dataset, not a single page')
    job_status: Literal['completed','failed','cancelled','scraping','unknown'] = 'unknown'
    next_cursor: str | None = Field(default=None, description='Explicit null means no remaining page; omission means unknown')
    seen_cursors: list[str] = Field(default_factory=list, max_length=5000)
    truncated: StrictBool = Field(default=None, description='Explicit false if caller knows no truncation occurred')

class Source(Input):
    id: str = Field(min_length=1,max_length=256)
    text: str

class Citation(Input):
    source_id: str = Field(min_length=1,max_length=256)
    quote: str = Field(min_length=1,max_length=10000)
    start: StrictInt = Field(default=None,ge=0)
    end: StrictInt = Field(default=None,ge=1)

class CitationInput(Input):
    sources: list[Source] = Field(max_length=100)
    citations: list[Citation] = Field(max_length=1000)
    required_source_ids: list[str] = Field(default_factory=list,max_length=100)

class UsageContext(Input):
    task_id: str = Field(min_length=1, max_length=256)
    purpose: Literal['real_task', 'test', 'demo', 'retry']
