# PawPrints Security Review

Review date: 7 July 2026  
Scope: the committed React/Electron frontend, FastAPI backend, vision adapters, local storage, query layer, and FFmpeg media pipeline.

## Executive summary

PawPrints has a sensible security baseline for a local hackathon application. Secrets remain server-side, local browser origins are allowlisted, model inputs are path-confined, pet images receive content checks, managed files use collision-safe or atomic writes, and FFmpeg commands avoid shell interpolation.

The current trust boundary is one user on one machine. The API has no authentication, rate limiting, global upload limit, or automatic retention policy for most artifacts. It should therefore remain bound to localhost and should not be deployed as a public service until the hardening actions below are complete.

## Threat model

Protected data includes:

- API keys and cloud credentials in `src/backend/.env`
- Uploaded home/pet videos and extracted frames
- Pet names and reference photos
- Activity timelines, query history, and generated proof/highlight videos

The expected actor is the local machine owner. Untrusted inputs are uploaded files, pet names, natural-language questions, model responses, stored JSON, and file paths derived from managed artifacts. External data processors may include Google, Anthropic, or OpenAI when the corresponding hosted model is selected. Ollama keeps the scene-description request local.

## Implemented controls

| Area | Implemented control | Evidence in code |
|---|---|---|
| Secrets | Keys load from environment variables and `.env` is ignored by Git. The frontend receives only provider names. | `vision_model/config.py`, `.gitignore`, `.env.example` |
| CORS | Browser access is limited to `localhost:5173` and `127.0.0.1:5173`. | `api/server.py` |
| Image validation | Pet images are limited to JPEG/PNG, 20 MB, non-empty content, and matching magic bytes. | `pet_profiles/store.py` |
| Path confinement | Profile image paths must remain under managed storage; vision inputs must remain under the allowed frame directory. | `pet_profiles/store.py`, `vision_model/image_validation.py` |
| Identifier safety | Jobs and query artifacts use generated IDs; proof IDs accept only letters, numbers, and hyphens. | `api/pipeline_runner.py`, `query_layer/proof_storage.py` |
| Safer process execution | FFmpeg receives an argument list with shell execution disabled; failures are captured and surfaced. | `media_tools.py` |
| Atomic/collision-safe output | Profile manifests, query responses, reels, and timelines avoid partial overwrites or filename collisions. | `pet_profiles/store.py`, `query_layer/response_storage.py`, `highlight_reel/output_storage.py`, `event_builder/timeline_storage.py` |
| Model isolation | The vision model is asked to describe the scene, while identity is decided separately with YOLO and CLIP. Registered names are revalidated before timeline storage. | `vision_model/prompt.py`, `identity_matcher.py`, `event_builder/clean_results.py` |
| Resource cancellation | A disconnected upload client signals the worker to stop at safe checkpoints. | `api/server.py`, `api/pipeline_runner.py` |
| Temporary proof cleanup | Expired managed proof clips are removed on later proof requests; the default lifetime is 24 hours. | `query_layer/proof_storage.py`, `query_layer/service.py` |
| Electron renderer boundary | No Node API is exposed through the empty preload bridge; Electron defaults retain context isolation and disable renderer Node integration. | `electron/main.js`, `electron/preload.js` |

## Findings and recommended actions

### SEC-01 - No API authentication or authorization (Medium locally; High if exposed)

Anyone who can reach the API can upload footage, read mounted media, create or delete pet profiles, rename pets, and query stored timelines. Uvicorn is started on localhost in the documented workflow, which keeps the current exposure narrow.

**Before network deployment:** add authenticated sessions or signed API tokens, per-user authorization, CSRF-aware browser controls, and private media delivery. Keep the service bound to `127.0.0.1` until then.

### SEC-02 - Video uploads have no explicit size, duration, or content limit (Medium)

Pet images are validated, but footage is persisted before OpenCV attempts to decode it. A very large or malformed upload can consume disk, CPU, memory, or model quota.

**Recommended:** reject unsupported containers, stream with a byte limit, probe duration/codec before processing, set per-job time and frame caps, and add rate/concurrency limits.

### SEC-03 - Sensitive local artifacts persist (Medium)

Uploads, candidate frames, timelines, query-response JSON, and highlight reels remain on disk. Only temporary query-proof clips have a cleanup policy, and cleanup runs when a later proof is requested.

**Recommended:** add a visible retention setting, scheduled cleanup, a one-click delete-history action, and clear consent text before sending a frame to a hosted provider. Encrypt storage when the device threat model requires it.

### SEC-04 - Static media routes are unauthenticated (Medium if network-exposed)

Mounted `/media/*` paths make source videos, frames, profile photos, results, and proofs directly retrievable by URL. Random job IDs reduce accidental guessing but are not access control.

**Recommended:** replace public static mounts with authenticated file endpoints or time-limited signed URLs in any shared deployment.

### SEC-05 - Dependencies are mostly unpinned and no automated vulnerability report is committed (Medium)

Python requirements do not pin exact versions, and the repository contains no Aikido, `pip-audit`, or npm audit artifact. Reproducibility and supply-chain review are therefore limited.

**Recommended:** create a tested lock file, pin direct dependencies, enable Dependabot or Renovate, and run Aikido plus ecosystem-native audits in CI.

### SEC-06 - Electron launcher contains a developer-specific interpreter path (Low security, High portability)

The hard-coded Python executable can make the desktop path fail on another machine. The empty preload bridge is a good starting boundary, but the window does not explicitly set `contextIsolation`, `nodeIntegration`, or `sandbox`.

**Recommended:** resolve the packaged interpreter at runtime and explicitly set `contextIsolation: true`, `nodeIntegration: false`, and `sandbox: true` before distribution.

### SEC-07 - Hosted AI providers receive candidate frames (Privacy consideration)

When Gemini, Claude, or OpenAI is selected, candidate images leave the local machine and are subject to the selected provider's account and retention terms. API keys remain backend-only, but the UI does not yet present a provider-specific disclosure.

**Recommended:** show a clear local-versus-cloud privacy label, obtain consent, minimize frames, document provider retention settings, and offer Ollama as the private default.

## Automated scan status

No Aikido scan export or badge was present in the repository during this review, so this document does **not** claim an Aikido pass. Before submission:

1. Connect the final repository and default branch to Aikido.
2. Run SAST, dependency, secret, and infrastructure checks that apply to the project.
3. Remediate or document accepted findings.
4. Export the result or add a shareable report link here and to the project report.

This honest status should be replaced with the real scan ID, date, commit hash, and finding counts once the scan is complete.

## Verification performed for this documentation pass

- Manual review of file-path handling, upload flows, static mounts, secrets, subprocess use, persistence, CORS, and Electron configuration.
- Frontend production build completed successfully: 70 modules transformed.
- Backend test discovery executed 89 tests in the isolated runner: 84 passed and 5 ended in environment/fixture errors (missing untracked compatibility JSON plus optional `torch` and `ollama` packages). No failing assertion was observed in that run.

## Safe judging configuration

- Run Uvicorn on its default loopback host and port 8000.
- Use test footage that contains no people, addresses, screens, or other unnecessary private information.
- Prefer Ollama for a fully local scene-description path, or use a restricted low-value API key for a hosted provider.
- Never commit `.env`, pet profiles, uploaded videos, extracted frames, or generated results.
- Delete local artifacts after the judging session if the footage is sensitive.

## Reporting a security issue

Do not include API keys, private footage, or exploit payloads in a public issue. Contact the project maintainers privately with the affected commit, reproduction steps, impact, and a minimal redacted proof of concept.
