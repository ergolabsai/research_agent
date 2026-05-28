# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from pydantic import BaseModel


class FigureRef(BaseModel):
    """Reference to a submitted figure. Bytes live in ObjectStorage; this carries the lookup keys.

    A figure has a required `submitted` image (what the paper shows) and an optional
    `predicted` image (a baseline the user supplies for the orchestrator to compare against).
    """

    name: str
    submitted_storage_key: str
    submitted_content_type: str
    predicted_storage_key: str | None = None
    predicted_content_type: str | None = None

    model_config = {"frozen": True}


class Paper(BaseModel):
    """A submitted paper. The unit of input to validation."""

    text: str
    title: str | None = None
    authors: list[str] | None = None
    abstract: str | None = None
    figures: list[FigureRef] = []
    bibliography: dict[str, str] | None = None

    model_config = {"frozen": True}
