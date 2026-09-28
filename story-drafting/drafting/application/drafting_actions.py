from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.domain as domain


class MapToDraftingSpec(ts.Mapper, domain.DraftingSpec):

    def __init__(self, keep_drafted_stories_request: relays.KeepDraftedStoriesRequest) -> None:
        super().__init__(
            drafting_id=keep_drafted_stories_request.drafting_id,
            job=keep_drafted_stories_request.job,
            step="drafting",
            stories=(),
            accepted_stories=(),
        )


class MapToDraftedStoriesSpec(ts.Mapper, domain.DraftedStoriesSpec):

    def __init__(self, keep_drafted_stories_request: relays.KeepDraftedStoriesRequest) -> None:
        super().__init__(texts=keep_drafted_stories_request.texts)


class MapToStoryRow(ts.Mapper, ports.StoryRow):

    def __init__(self, story: domain.Story) -> None:
        super().__init__(story_id=str(story.identity), text=str(story.text))


class MapToDraftingRow(ts.Mapper, ports.DraftingRow):

    def __init__(self, drafting: domain.Drafting) -> None:
        super().__init__(
            drafting_id=str(drafting.identity),
            job=str(drafting.job),
            step=str(drafting.step),
            stories=tuple(MapToStoryRow(story) for story in drafting.stories),
            accepted_stories=tuple(MapToStoryRow(story) for story in drafting.accepted_stories),
        )


class MapToSaveDraftingRequest(ts.Mapper, ports.SaveDraftingRequest):

    def __init__(self, drafting: domain.Drafting) -> None:
        super().__init__(drafting_row=MapToDraftingRow(drafting))


class MapToKeepDraftedStoriesResponse(ts.Mapper, relays.KeepDraftedStoriesResponse):

    def __init__(self, save_drafting_response: ports.SaveDraftingResponse) -> None:
        super().__init__(drafting_id=save_drafting_response.drafting_id)


class DraftingActions(ts.Actions):

    def __init__(self, drafting_store: ports.DraftingStore) -> None:
        self._drafting_store = drafting_store

    async def keep_drafted_stories(
        self, keep_drafted_stories_request: relays.KeepDraftedStoriesRequest
    ) -> relays.KeepDraftedStoriesResponse:
        drafting = domain.Drafting(MapToDraftingSpec(keep_drafted_stories_request))
        drafting.draft(domain.DraftedStories(MapToDraftedStoriesSpec(keep_drafted_stories_request)))
        async with self._drafting_store.transaction() as drafting_repository:
            save_drafting_response = await drafting_repository.save_drafting(MapToSaveDraftingRequest(drafting))
        return MapToKeepDraftedStoriesResponse(save_drafting_response)
