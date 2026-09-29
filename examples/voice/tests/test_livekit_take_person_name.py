from __future__ import annotations

import asyncio
import os
import pathlib
import sys

import pytest

import protocol
import simulated.person as simulated_person


class TestTakePersonName:
    async def test_the_agent_asks_hears_and_greets_the_person_by_the_name_it_heard(self) -> None:
        if os.environ.get("VOICE_EVALS") != "1":
            pytest.skip("set VOICE_EVALS=1 and run scripts/verify voice with LiveKit credentials, Postgres and Restate")
        tree = pathlib.Path(__file__).resolve().parent.parent
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        for person_name in ("Sarah", "David", "Michael"):
            person = simulated_person.Person(
                url=os.environ["LIVEKIT_URL"],
                api_key=os.environ["LIVEKIT_API_KEY"],
                api_secret=os.environ["LIVEKIT_API_SECRET"],
                agent_name=os.environ["LIVEKIT_AGENT_NAME"],
                name=person_name,
                answers=simulated_person.WHEN_ASKED,
            )
            answering = asyncio.create_task(person.answer())
            try:
                placing = await asyncio.create_subprocess_exec(
                    sys.executable, "-m", "srv.cli.main", "place-call",
                    cwd=tree, env=env, stdout=asyncio.subprocess.PIPE,
                )
                placed, _ = await asyncio.wait_for(placing.communicate(), 180.0)
                await asyncio.wait_for(answering, 30.0)
            finally:
                answering.cancel()
                await asyncio.gather(answering, return_exceptions=True)
            placed_response = protocol.CliResponse(
                exit_code=placing.returncode or 0, line=protocol.Line(text=placed.decode().strip())
            )
            cli_request = protocol.CliRequest(args=(placed_response.line.text,))
            getting = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "srv.cli.main", "get-call", *cli_request.args,
                cwd=tree, env=env, stdout=asyncio.subprocess.PIPE,
            )
            got, _ = await getting.communicate()
            lookup_response = protocol.CliResponse(
                exit_code=getting.returncode or 0, line=protocol.Line(text=got.decode().strip())
            )

            assert placed_response.exit_code == 0, placed_response
            assert person.room_name == placed_response.line.text
            assert lookup_response == protocol.CliResponse(exit_code=0, line=protocol.Line(text=person_name))
            assert person.heard, person.said
            assert person_name.casefold() in person.heard[-1].casefold(), person.heard

    async def test_the_person_hears_the_whole_goodbye_before_the_line_drops(self) -> None:
        if os.environ.get("VOICE_EVALS") != "1":
            pytest.skip("set VOICE_EVALS=1 and run scripts/verify voice with LiveKit credentials, Postgres and Restate")
        tree = pathlib.Path(__file__).resolve().parent.parent
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        person = simulated_person.Person(
            url=os.environ["LIVEKIT_URL"],
            api_key=os.environ["LIVEKIT_API_KEY"],
            api_secret=os.environ["LIVEKIT_API_SECRET"],
            agent_name=os.environ["LIVEKIT_AGENT_NAME"],
            name="Sarah",
            answers=simulated_person.WHEN_ASKED,
        )
        answering = asyncio.create_task(person.answer())
        try:
            placing = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "srv.cli.main", "place-call",
                cwd=tree, env=env, stdout=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(placing.communicate(), 180.0)
            await asyncio.wait_for(answering, 30.0)
        finally:
            answering.cancel()
            await asyncio.gather(answering, return_exceptions=True)

        heard_at = [at for at, (kind, _) in enumerate(person.events) if kind == simulated_person.HEARD]
        dropped_at = [at for at, (kind, _) in enumerate(person.events) if kind == simulated_person.DROPPED]
        assert placing.returncode == 0
        assert heard_at and dropped_at, person.events
        assert heard_at[-1] < dropped_at[0], person.events
        assert "sarah" in person.events[heard_at[-1]][1].casefold(), person.events
        assert person.events[dropped_at[0]][1] == "ROOM_DELETED", person.events

    async def test_an_answer_spoken_over_the_question_is_not_lost(self) -> None:
        if os.environ.get("VOICE_EVALS") != "1":
            pytest.skip("set VOICE_EVALS=1 and run scripts/verify voice with LiveKit credentials, Postgres and Restate")
        tree = pathlib.Path(__file__).resolve().parent.parent
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        person = simulated_person.Person(
            url=os.environ["LIVEKIT_URL"],
            api_key=os.environ["LIVEKIT_API_KEY"],
            api_secret=os.environ["LIVEKIT_API_SECRET"],
            agent_name=os.environ["LIVEKIT_AGENT_NAME"],
            name="Sarah",
            answers=simulated_person.OVER_THE_QUESTION,
        )
        answering = asyncio.create_task(person.answer())
        try:
            placing = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "srv.cli.main", "place-call",
                cwd=tree, env=env, stdout=asyncio.subprocess.PIPE,
            )
            placed, _ = await asyncio.wait_for(placing.communicate(), 180.0)
            await asyncio.wait_for(answering, 30.0)
        finally:
            answering.cancel()
            await asyncio.gather(answering, return_exceptions=True)
        cli_request = protocol.CliRequest(args=(placed.decode().strip(),))
        getting = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "srv.cli.main", "get-call", *cli_request.args,
            cwd=tree, env=env, stdout=asyncio.subprocess.PIPE,
        )
        got, _ = await getting.communicate()
        cli_response = protocol.CliResponse(
            exit_code=getting.returncode or 0, line=protocol.Line(text=got.decode().strip())
        )

        assert placing.returncode == 0
        assert person.said == ["Sarah."], person.said
        assert cli_response == protocol.CliResponse(exit_code=0, line=protocol.Line(text="Sarah"))
        assert "sarah" in person.heard[-1].casefold(), person.heard
