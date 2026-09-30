from __future__ import annotations

import asyncio
import os
import subprocess
import sys

import simulated.person as simulated_person


class TestTakePersonName:
    async def test_the_agent_asks_hears_and_greets_the_person_by_the_name_it_heard(
        self, voice_evals: None, livekit_environ: dict[str, str], storage_url: str, host_engine_url: str, agent_server: str
    ) -> None:
        env = {
            **os.environ,
            **livekit_environ,
            "PYTHONPATH": os.pathsep.join(sys.path),
            "CALLS_STORAGE": storage_url,
            "RESTATE_URL": host_engine_url,
        }
        for person_name in ("Sarah", "David", "Michael"):
            person = simulated_person.Person(
                url=livekit_environ["LIVEKIT_URL"],
                api_key=livekit_environ["LIVEKIT_API_KEY"],
                api_secret=livekit_environ["LIVEKIT_API_SECRET"],
                agent_name=agent_server,
                name=person_name,
                answers=simulated_person.WHEN_ASKED,
            )
            answering = asyncio.create_task(person.answer())
            try:
                placed = await asyncio.to_thread(
                    subprocess.run,
                    [sys.executable, "-m", "srv.cli.main", "place-call"],
                    capture_output=True, text=True, check=False, env=env, timeout=180.0,
                )
                await asyncio.wait_for(answering, 30.0)
            finally:
                answering.cancel()
                await asyncio.gather(answering, return_exceptions=True)
            got = subprocess.run(
                [sys.executable, "-m", "srv.cli.main", "get-call", *placed.stdout.splitlines()],
                capture_output=True, text=True, check=False, env=env, timeout=180.0,
            )

            assert placed.returncode == 0, placed.stderr
            assert placed.stdout.splitlines() == [person.room_name]
            assert (got.returncode, got.stdout.splitlines()) == (0, [person_name]), got.stderr
            assert person.heard, person.said
            assert person_name.casefold() in person.heard[-1].casefold(), person.heard

    async def test_the_person_hears_the_whole_goodbye_before_the_line_drops(
        self, voice_evals: None, livekit_environ: dict[str, str], storage_url: str, host_engine_url: str, agent_server: str
    ) -> None:
        env = {
            **os.environ,
            **livekit_environ,
            "PYTHONPATH": os.pathsep.join(sys.path),
            "CALLS_STORAGE": storage_url,
            "RESTATE_URL": host_engine_url,
        }
        person = simulated_person.Person(
            url=livekit_environ["LIVEKIT_URL"],
            api_key=livekit_environ["LIVEKIT_API_KEY"],
            api_secret=livekit_environ["LIVEKIT_API_SECRET"],
            agent_name=agent_server,
            name="Sarah",
            answers=simulated_person.WHEN_ASKED,
        )
        answering = asyncio.create_task(person.answer())
        try:
            placed = await asyncio.to_thread(
                    subprocess.run,
                    [sys.executable, "-m", "srv.cli.main", "place-call"],
                    capture_output=True, text=True, check=False, env=env, timeout=180.0,
                )
            await asyncio.wait_for(answering, 30.0)
        finally:
            answering.cancel()
            await asyncio.gather(answering, return_exceptions=True)

        heard_at = [at for at, (kind, _) in enumerate(person.events) if kind == simulated_person.HEARD]
        dropped_at = [at for at, (kind, _) in enumerate(person.events) if kind == simulated_person.DROPPED]
        assert placed.returncode == 0, placed.stderr
        assert heard_at and dropped_at, person.events
        assert heard_at[-1] < dropped_at[0], person.events
        assert "sarah" in person.events[heard_at[-1]][1].casefold(), person.events
        assert person.events[dropped_at[0]][1] == "ROOM_DELETED", person.events

    async def test_an_answer_spoken_over_the_question_is_not_lost(
        self, voice_evals: None, livekit_environ: dict[str, str], storage_url: str, host_engine_url: str, agent_server: str
    ) -> None:
        env = {
            **os.environ,
            **livekit_environ,
            "PYTHONPATH": os.pathsep.join(sys.path),
            "CALLS_STORAGE": storage_url,
            "RESTATE_URL": host_engine_url,
        }
        person = simulated_person.Person(
            url=livekit_environ["LIVEKIT_URL"],
            api_key=livekit_environ["LIVEKIT_API_KEY"],
            api_secret=livekit_environ["LIVEKIT_API_SECRET"],
            agent_name=agent_server,
            name="Sarah",
            answers=simulated_person.OVER_THE_QUESTION,
        )
        answering = asyncio.create_task(person.answer())
        try:
            placed = await asyncio.to_thread(
                    subprocess.run,
                    [sys.executable, "-m", "srv.cli.main", "place-call"],
                    capture_output=True, text=True, check=False, env=env, timeout=180.0,
                )
            await asyncio.wait_for(answering, 30.0)
        finally:
            answering.cancel()
            await asyncio.gather(answering, return_exceptions=True)
        got = subprocess.run(
            [sys.executable, "-m", "srv.cli.main", "get-call", *placed.stdout.splitlines()],
            capture_output=True, text=True, check=False, env=env, timeout=180.0,
        )

        assert placed.returncode == 0, placed.stderr
        assert person.said == ["Sarah."], person.said
        assert (got.returncode, got.stdout.splitlines()) == (0, ["Sarah"]), got.stderr
        assert "sarah" in person.heard[-1].casefold(), person.heard
