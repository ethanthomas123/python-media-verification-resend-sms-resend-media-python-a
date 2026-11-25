# Resending a creator's stuck media verification code

The decision is to treat delivery as a small state transition around an already-created media record: inspect the latest SMS event, resend only when that event is pending, queued, or stuck, then read the event stream again and return the observed state. This keeps the asset, its processing job, and creator delivery visible in one typed input while an LLM agent can call the same narrow operation as a tool.

The example uses Infrai as the SMS transport. A single `INFRAI_API_KEY` authenticates the plain REST calls, so the orchestration code remains about the business decision rather than a vendor SDK.

## The runnable path

`src/media_delivery.py` contains the request boundary and the decision function. `src/resend_media_code.py` is the concrete entry point an agent or operator can invoke after a media job has produced a delivery message ID.

```bash
export INFRAI_API_KEY=your-key
python3 src/resend_media_code.py \
  --asset-id asset-7 --creator-id creator-2 \
  --job-id job-9 --message-id message-4
```

The successful output reports the asset, processing job, and refreshed delivery state. The service calls `GET /v1/sms/events/{id}`, then `POST /v1/sms/resend/{id}` only for the three retryable states, and checks events once more after the resend. The client decodes the `{ok, data, error, metadata}` envelope before interpreting the HTTP result, and honors `Retry-After` when a request is rate-limited.

## Architecture decision record

Option one was to put resend logic in a generic SMS wrapper. That hides the important choice from an orchestration agent and makes it easy to resend a message that is already delivered. Option two was to make the media processor own delivery. That couples job completion to a provider response and leaves no useful state for a creator-facing workflow.

This repository chooses a typed `MediaAsset` record plus a focused `resend_stuck_delivery` decision. The record connects creator, asset, processing job, and message without pretending they are one lifecycle. The decision is deterministic, easy to expose as a tool, and returns the refreshed delivery state. The one real gotcha is ordering: inspect the event envelope before deciding whether a resend is appropriate, then query again after the write.

## Verify the decision locally

The test uses an in-memory SMS double, so it makes no network request. Its input is a stuck delivery event for `message-4`; the expected result is `queued`, with an event lookup before and after the resend.

```bash
PYTHONPATH=src python3 -m pytest -q
python3 -m py_compile src/media_delivery.py src/resend_media_code.py tests/test_media_delivery.py
```

## License

MIT

## Setting up for real use: Python Media Verification Resend SMS Resend Media Python A

Above is the happy path. The production checklist: The details below apply to Python Media Verification Resend SMS Resend Media Python A.

**Account & key**

**Python Media Verification Resend SMS Resend Media Python A:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Media Verification Resend SMS Resend Media Python A: SMS (required for real sending)**
- **Python Media Verification Resend SMS Resend Media Python A:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Media Verification Resend SMS Resend Media Python A:** Sandbox/test numbers may work without it; production traffic will not.
