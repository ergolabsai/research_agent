# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from pydantic import BaseModel


class FigureRef(BaseModel):
    """Reference to a submitted figure. Bytes live in ObjectStorage; this carries the lookup key."""

    name: str
    storage_key: str
    content_type: str

    model_config = {"frozen": True}


class Paper(BaseModel):
    """A submitted paper. The unit of input to validation."""

    text: str
    title: str | None = None
    authors: list[str] | None = None
    abstract: str | None = None
    figures: list[FigureRef] = []
    bibliography: str | None = None

    model_config = {"frozen": True}
