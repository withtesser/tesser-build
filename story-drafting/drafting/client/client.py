from __future__ import annotations

import typing

import tesser.context as ts


class DraftStoriesRequest(ts.Request):

    def __init__(self, job: str) -> None:
        self.job = job


class DraftStoriesResponse(ts.Response):

    def __init__(self, drafting_id: str) -> None:
        self.drafting_id = drafting_id


class DraftedStory(ts.Response):

    def __init__(self, story_id: str, text: str) -> None:
        self.story_id = story_id
        self.text = text


class Drafting(ts.Response):

    def __init__(
        self,
        drafting_id: str,
        step: str,
        stories: tuple[DraftedStory, ...],
        accepted_stories: tuple[DraftedStory, ...],
    ) -> None:
        self.drafting_id = drafting_id
        self.step = step
        self.stories = stories
        self.accepted_stories = accepted_stories


class GetDraftingRequest(ts.Request):

    def __init__(self, drafting_id: str) -> None:
        self.drafting_id = drafting_id


class GetDraftingResponse(ts.Response):

    def __init__(self, drafting: Drafting) -> None:
        self.drafting = drafting


class DraftingRejected(ts.Error):

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class DraftingNotFound(ts.Error):

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


ERRORS: typing.Final[tuple[type[DraftingRejected], type[DraftingNotFound]]] = (DraftingRejected, DraftingNotFound)


class DraftingClient(ts.Client, typing.Protocol):

    async def draft_stories(self, draft_stories_request: DraftStoriesRequest) -> DraftStoriesResponse: ...

    async def get_drafting(self, get_drafting_request: GetDraftingRequest) -> GetDraftingResponse: ...
