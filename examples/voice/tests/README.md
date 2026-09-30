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

A plain `pytest` from `examples/voice` runs every tier, including this one,
with nothing served beforehand: the root `conftest.py` starts a private
Postgres and private Restate engines (containers, so Docker is needed) and
removes them at the end. This tier's tests skip unless `VOICE_EVALS=1`,
because they use paid LiveKit/model APIs, and a normal run starts nothing for
them. To run them, set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and
`LIVEKIT_API_SECRET` for a test project and a unique `LIVEKIT_AGENT_NAME`,
then run from `examples/voice`:

```sh
VOICE_EVALS=1 LIVEKIT_AGENT_NAME=caller-acceptance pytest tests
```

Use an agent name not served by another worker. For this tier the fixtures
start a second private Restate engine (the context tests register the
component's own names on the first), serve the production Restate host
(`srv.restate.main`) as a subprocess registered with it, and serve the
production LiveKit agent server (`srv.livekit.agent_server`) under that agent
name. The tests are clients of both hosts, and each one runs the CLI host
(`subprocess.run` of `python -m srv.cli.main`) once per command, with an
environment built from the fixtures: it places a call through `place-call`
while a simulated person (`simulated/person.py`, a directory the analyzer does
not govern) watches LiveKit for the room the agent was dispatched into, joins
it as `person`, and answers either when asked or over the question.
