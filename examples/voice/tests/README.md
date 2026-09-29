# Voice acceptance tests

The automated name-taking test plays the user: it never loads the
application in its own process. It places each call by running the CLI host
(`python -m srv.cli.main place-call`, which prints the call id) as a
subprocess, and reads the saved name back through the same host
(`python -m srv.cli.main get-call <call_id>`, which prints the person's name),
reading its exit code and output lines. Behind the hosts run the production clients,
gateways, Restate workflow/actions, and Postgres repository. Three simulated
people join real LiveKit rooms and reply with model-generated speech. No SIP
trunk or telephone number is needed.

The test checks each saved name through `get-call` and checks the final agent
transcription received by the person in the room. It does not independently
transcribe the agent's audio. The simulated person is instructed to provide
their name only when asked.

Start the local Postgres and Restate services described in `scripts/verify`.
Set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` for a test project,
then run from the repository root:

```sh
VOICE_EVALS=1 LIVEKIT_AGENT_NAME=caller-acceptance scripts/verify voice
```

Use an agent name not served by another worker. The verification script runs
in three steps: first every tier but this one (`pytest --ignore=tests`, which works because `testpaths` leaves `tests` out) with no
host served; then it starts the production Restate HTTP host and registers it
with Restate (forcing over whatever the context tests registered), and with
`VOICE_EVALS=1` also starts the production LiveKit agent server
(`srv.livekit.agent_server`) under that agent name; last it runs this tier
(`pytest tests`). The tests are clients of both hosts, and each one runs the
CLI host (`subprocess.run` of `python -m srv.cli.main`) once per command: it places a call
through `place-call` while a simulated person
(`simulated/person.py`, a directory the analyzer does not govern) watches
LiveKit for the room the agent was dispatched into, joins it as `person`, and
answers either when asked or over the question.

Defaults are Postgres at `localhost:5434` and Restate (calls/admin) at
`localhost:28080`/`localhost:29070`. Override them with `CALLS_STORAGE`,
`RESTATE_URL`, and `RESTATE_ADMIN`. This test uses paid LiveKit/model APIs
and is skipped unless `VOICE_EVALS=1`.
