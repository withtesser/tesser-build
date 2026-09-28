from __future__ import annotations

import tesser.component as ts

import drafting.application as application
import drafting.client as client


class Spec(ts.Spec):

    def __init__(self, ingress: str, drafter: str) -> None:
        self.ingress = ingress
        self.drafter = drafter


class Config(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.ingress = spec.ingress
        self.drafter = spec.drafter


class Drafting(ts.Component):

    class Client:

        def __init__(self, drafting_service: application.DraftingService) -> None:
            self._drafting_service = drafting_service

        async def draft_stories(
            self, draft_stories_request: client.DraftStoriesRequest
        ) -> client.DraftStoriesResponse:
            return await self._drafting_service.draft_stories(draft_stories_request)

        async def get_drafting(self, get_drafting_request: client.GetDraftingRequest) -> client.GetDraftingResponse:
            return await self._drafting_service.get_drafting(get_drafting_request)

    def __init__(self, config: Config) -> None:
        self.client: client.DraftingClient = Drafting.Client(application.DraftingService())

    async def close(self) -> None:
        return None
