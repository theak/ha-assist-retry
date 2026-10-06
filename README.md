# Assist Retry

A Home Assistant conversation agent that passes each request to another agent, and asks it again
when it fails before saying anything. Put it in front of a cloud LLM agent (Google Gemini, OpenAI,
Anthropic, Ollama and so on) so that an occasional API error or malformed reply doesn't end in
your voice satellite's error tone.

## What it retries

An attempt is retried when the wrapped agent raises an error or returns an error response
**before producing any text**. That covers things like:

- API timeouts and "model overloaded" errors, which Home Assistant would otherwise speak as
  "Sorry, I had a problem talking to …"
- malformed replies, such as a model calling a tool when none is configured (Home Assistant
  fails the request with `No LLM API configured`)

Once the agent has produced text, a failure is passed through as before: that text may already
be on its way to the speaker, so it can't be taken back.

Each retry logs a warning, so you can see how often it happens.

## How it works

The agent runs the wrapped agent inside the same conversation, so:

- streamed text still reaches the voice pipeline as it arrives, and text-to-speech engines that
  accept streamed text still start speaking early
- conversation history and follow-up questions work as usual
- local commands are unaffected: with "Prefer handling commands locally" on, Home Assistant
  handles them before any agent is called

In normal use it adds no noticeable delay. A retried request takes as long as the failed attempt
plus a new answer.

It's meant for LLM agents. Wrapping Home Assistant's own agent only adds a retry to
"Sorry, I couldn't understand that".

> [!WARNING]
> This relies on internal parts of Home Assistant's conversation component (how the active
> conversation is shared, and the listener that streams text to the voice pipeline). A Home
> Assistant update could change them. If the agent starts failing after an upgrade, point your
> voice assistant back at the original agent and check the
> [issues](https://github.com/theak/ha-assist-retry/issues). A weekly check in this repo runs
> against the newest Home Assistant release to catch that early.

## Install with HACS

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/theak/ha-assist-retry` with
   type **Integration**.
2. Download **Assist Retry** and restart Home Assistant.
3. **Settings → Devices & services → Add integration → Assist Retry.** Pick the agent to wrap
   and the number of retries (1 is usually enough).
4. **Settings → Voice assistants**, open your assistant and set its conversation agent to the
   new "… (with retry)" agent.

To install by hand instead, copy `custom_components/assist_retry` into your
`config/custom_components/` folder and continue from step 2.

To change the agent or the number of retries later, use **Configure** on the integration.

## Testing it

The `assist_retry.simulate_failure` action makes the next attempts fail without calling the
wrapped agent. Run it with `count: 1`, then ask your voice assistant something: you should get a
normal answer, and a "retrying" warning in the log.

```yaml
action: assist_retry.simulate_failure
data:
  count: 1
```

## License

MIT
