from __future__ import annotations

import tesser.application as ts

import drafting.application.ports as ports
import drafting.application.relays as relays
import drafting.domain as domain


class MapToRunSpec(ts.Mapper, domain.RunSpec):

    def __init__(self, keep_run_request: relays.KeepRunRequest) -> None:
        super().__init__(run_id=keep_run_request.run_id, job=keep_run_request.job)


class MapToRunSpecFromOfferStoriesRequest(ts.Mapper, domain.RunSpec):

    def __init__(self, offer_stories_request: relays.OfferStoriesRequest) -> None:
        super().__init__(run_id=offer_stories_request.run_id, job=offer_stories_request.job)


class MapToDraftedStoriesSpec(ts.Mapper, domain.DraftedStoriesSpec):

    def __init__(self, offer_stories_request: relays.OfferStoriesRequest) -> None:
        super().__init__(stories=offer_stories_request.stories)


class MapToSaveRunRequest(ts.Mapper, ports.SaveRunRequest):

    def __init__(self, run: domain.Run) -> None:
        super().__init__(
            run_id=str(run.identity),
            job=str(run.job),
            stage=str(run.stage),
            stories=tuple(str(story) for story in run.stories),
        )


class MapToKeepRunResponse(ts.Mapper, relays.KeepRunResponse):

    def __init__(self, save_run_response: ports.SaveRunResponse) -> None:
        super().__init__(run_id=save_run_response.run_id)


class MapToOfferStoriesResponse(ts.Mapper, relays.OfferStoriesResponse):

    def __init__(self, save_run_response: ports.SaveRunResponse) -> None:
        super().__init__(run_id=save_run_response.run_id)


class RunActions(ts.Actions):

    def __init__(self, run_repository: ports.RunRepository) -> None:
        self._run_repository = run_repository

    async def keep_run(self, keep_run_request: relays.KeepRunRequest) -> relays.KeepRunResponse:
        run = domain.Run(MapToRunSpec(keep_run_request))
        save_run_response = await self._run_repository.save_run(MapToSaveRunRequest(run))
        return MapToKeepRunResponse(save_run_response)

    async def offer_stories(self, offer_stories_request: relays.OfferStoriesRequest) -> relays.OfferStoriesResponse:
        run = domain.Run(MapToRunSpecFromOfferStoriesRequest(offer_stories_request))
        run.offer_stories(domain.DraftedStories(MapToDraftedStoriesSpec(offer_stories_request)))
        save_run_response = await self._run_repository.save_run(MapToSaveRunRequest(run))
        return MapToOfferStoriesResponse(save_run_response)
