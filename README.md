# Home Assistant Assist Retry

Home Assistant doesn't have a built-in retry functionality for Assist entities, so something like a temporal Gemini/LLM error results in requests failing. This allows you create a new conversation agent that wraps another conversational LLM agent (e.g. Gemini, OpenAI, etc) with retry logic, so things retry instead of erroring out. Each retry logs a warning, so you can see how often it happens. There's no latency impact, unless a retry is necessary:
<img width="517" height="404" alt="image" src="https://github.com/user-attachments/assets/c884902b-e15c-4d47-9768-4af685d6976f" />


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
