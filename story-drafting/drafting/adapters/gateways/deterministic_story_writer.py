from __future__ import annotations

import typing

import tesser.adapters as ts

import drafting.application.ports as ports

_STORIES: typing.Final[tuple[str, ...]] = (
    "As a developer, I want to start the work on this job: {job}, so that the agent begins from what I need.",
    "As a developer, I want to weigh in at a fixed checkpoint on this job: {job}, so that nothing is built "
    "before I agree.",
    "As a developer, I want to come back to this job where we left it: {job}, so that I never re-explain it.",
)


class DeterministicStoryWriter(ts.Gateway):

    async def write_stories(self, write_stories_request: ports.WriteStoriesRequest) -> ports.WriteStoriesResponse:
        return ports.WriteStoriesResponse(texts=tuple(story.format(job=write_stories_request.job) for story in _STORIES))
