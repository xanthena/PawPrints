# Security and Privacy Risk Audit

Audit scope: current working tree, tracked artifacts, configuration templates,
relevant git history, upload/path boundaries, provider routing, FFmpeg
subprocesses, and frontend/backend boundary.

No populated Gemini, Anthropic, OpenAI, Google, or private-key credential was
found in the current tree or in the searched git history. `.env` is ignored and
`.env.example` contains empty placeholders. The findings below are genuine
risks despite the absence of an exposed API key.

## High: the pinned frontend toolchain has current advisories

An `npm audit --package-lock-only` run on 2026-07-06 reported two high-severity
packages and one moderate package in the locked dependency graph:

- Electron 31.7.7 is affected by multiple Electron advisories, including
  use-after-free and renderer/IPC issues; npm's available remediation is the
  semver-major Electron 43.0.0 upgrade.
- Vite 5.4.21 is affected by Windows path/deny-list bypass and optimized source
  map path traversal advisories; npm's remediation is the semver-major Vite
  8.1.3 upgrade.
- esbuild is a moderate transitive finding involving development-server request
  access and is remediated through the Vite upgrade.

Do not expose the Vite development server to untrusted networks. Plan and test
the Electron/Vite major upgrades separately because they can change packaging,
Node, plugin, and preload behavior.
## High: user video and derived private media are committed

The repository currently tracks a roughly 102 MB source MP4, extracted CCTV
frames, multiple proof MP4s, a highlight MP4, raw vision JSON, timelines, and
query results. These artifacts can reveal home interiors, routines, people, pet
identity, and timestamps. Git ignore rules do not remove files that were
already committed, so adding ignore entries only protects future untracked
artifacts.

Before using real customer footage, remove generated/private media from git
history with an agreed history-rewrite process, rotate any affected remote
copies, and use private application storage with a retention policy. Keep only
explicitly reviewed synthetic/demo fixtures, ideally small and clearly marked.

## Medium: a tracked manifest exposes a local username and path

`src/results/highlight-reel/highlight_reel_manifest.json` contains absolute
paths beginning with `C:\Users\Riz\...`. This leaks workstation layout and a
user identifier and demonstrates that generated artifacts are being committed.
New API-facing output should use artifact IDs or repository/application-relative
paths. Existing tracked history still retains the old absolute value until
history is cleaned.

## Medium: arbitrary roots can leak filesystem layout in query JSON

`relative_repo_path()` uses `os.path.relpath()` even when an injected timeline,
video, proof, or response path is outside the repository. That can produce
`../../...` paths. `source_video_error` can also include an absolute local path.
This is useful in local tests but should not cross a future UI/API trust
boundary. A transport serializer should reject paths outside managed roots and
return opaque artifact IDs plus sanitized error codes/messages.

## Medium: pet identity photos are sensitive and stored unencrypted

The profile module validates type, size, count, and path containment and copies
references into managed storage, but the files and manifest are plaintext.
Anyone with access to the user account or application-data folder can read
them. Define deletion/retention behavior, use OS-appropriate private file
permissions, and consider encryption at rest if the threat model includes
other local users or device theft. Never commit `src/data/pet_profiles`.

## Medium: fallback routing can send images to a second provider

The model router retries the configured fallback on any primary exception. A
candidate frame and all registered cat reference photos are then sent to the
fallback model as well. This behavior is functional, but it is a privacy
boundary if primary and fallback are different remote vendors. The UI should
show which providers may receive images and require an explicit policy/consent
for cross-provider fallback. Logs and responses should record the provider used
without printing credentials or full provider error payloads.

## Medium: untrusted media reaches native parsers

Uploaded videos will be parsed by OpenCV and FFmpeg, and uploaded reference
images are eventually decoded by model/provider tooling. The new profile store
checks extension, size, header signature, and managed paths, but a valid header
does not prove a file is safe. Keep OpenCV/FFmpeg current, impose upload and
duration/resolution limits, run media work with least privilege, use timeouts,
and isolate it from secrets when processing untrusted files.

## Low/medium: Python dependency versions and audits are incomplete

The npm lockfile pins the frontend tree and was audited above, but Python
requirements are mostly unbounded. Rebuilding later can silently install
incompatible or vulnerable releases. Pin tested Python versions and hashes, and
run both npm and Python vulnerability scans in CI.

## Low: temporary proof cleanup is opportunistic

Proof MP4s default to a 24-hour TTL, but cleanup only runs when another proof is
created. On an inactive installation, expired private clips remain on disk.
Schedule cleanup at application startup/interval and include all derived frames,
raw model JSON, highlights, and query archives in the product retention policy.

## Positive controls already present

- Provider clients are lazy and keys come from environment variables.
- `.env` and newly added pet/source/result paths are ignored for future files.
- Candidate image validation enforces an allowed directory, type, non-empty
  content, and a size limit.
- Pet-profile manifest paths are relative and checked against managed storage.
- FFmpeg is invoked with an argument list and `shell=False`; subtitle text is
  passed through a temporary file instead of shell interpolation.
- Query proof failures do not erase textual evidence, limiting pressure to
  weaken error handling.

