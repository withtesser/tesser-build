from __future__ import annotations

import pytest

import drafting.application as application
import drafting.client as client


class TestDraftingService:

    async def test_drafting_stories_is_not_implemented_yet(self) -> None:
        with pytest.raises(NotImplementedError):
            await application.DraftingService().draft_stories(client.DraftStoriesRequest(job="a job"))

    async def test_getting_a_drafting_is_not_implemented_yet(self) -> None:
        with pytest.raises(NotImplementedError):
            await application.DraftingService().get_drafting(client.GetDraftingRequest(drafting_id="d1"))
