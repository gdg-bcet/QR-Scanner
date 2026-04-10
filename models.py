"""Pydantic models for the T-Shirt Distribution API."""

from pydantic import BaseModel
from typing import Dict, Optional


class PersonStatus(BaseModel):
    """Response model for a single person's status."""
    token_id: str
    name: str
    email: str
    profile_url: str
    department: str
    graduation_year: str
    tshirt_size: str
    is_taken: bool


class SizeBreakdown(BaseModel):
    """Breakdown of t-shirt sizes."""
    total: int
    taken: int
    remaining: int


class StatsResponse(BaseModel):
    """Response model for overall statistics."""
    total: int
    taken: int
    remaining: int
    by_size: Dict[str, SizeBreakdown]


class ActionResponse(BaseModel):
    """Response model for mark/reset actions."""
    success: bool
    message: str
    person: Optional[PersonStatus] = None
