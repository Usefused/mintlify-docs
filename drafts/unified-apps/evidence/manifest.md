# Evidence manifest

Research date: 2026-10-11.
Public sources: https://usefused.com/docs/llms.txt (discovery index); https://github.com/Usefused/cli/releases (released CLI provenance).
No product behavior will be inferred from local implementation files.

## Accepted public sources

- https://usefused.com/docs/app/unified-apps — accessed 2026-10-11; authored TypeScript, operation selection, plan/apply, family execution URL, credentials, version promotion and consumer references. Snapshot: public-unified-apps.md.
- https://usefused.com/docs/app/from-a-prompt — accessed 2026-10-11; natural-language drafting, review before apply, apply versus execution. Snapshot: public-from-a-prompt.md.
- https://usefused.com/docs/app/testing/over-rest — accessed 2026-10-11; execution request and response conventions. Snapshot: public-rest.md. Unified App family-ID guidance comes from the dedicated Unified Apps page, which is more precise than the generic SDK REST example.
- https://github.com/Usefused/cli/releases/tag/v0.41.1 — published 2026-10-05; installed binary reports 0.41.1. Executable is outside source checkout. `version` subcommand fails; public `--version` succeeds.

Initial web-tool fetch failed; public pages were retrieved directly over HTTPS. No private source checkout substituted.

## Demo discovery

Released CLI service discovery found public Frankfurter version 2.1.1 and exact `getRate` operation, GET `/rate/{base}/{quote}`, with optional `date` and `providers` parameters and an unauthenticated security requirement. Synthetic demo chosen: convert 100 EUR to USD on a fixed historical date, returning amount, currencies, rate, rate date, and converted amount.
The hosted Engine UI is accessible using the existing authorized CLI credential. Authentication is excluded from recording. No credential was added to article evidence.

UI draft generation produced source and selected Frankfurter/getRate, but the assistant's final message ended with an HTTP 500. This is not treated as a clean successful AI chat demonstration. The draft remained editable. The source was simplified and reviewed explicitly before validation. The first attempted background recorder could not capture outside an active tool context; its frame count was zero. Subsequent capture segments use real timed browser screenshots inside each active tool call. The failed chat segment is excluded from the deliverable recording.

## Hosted validation boundary

UI action: Validate and compile, 2026-10-11.
Observed result: “This workspace has reached its Unified App limit (2 of 2). Deactivate an unused Unified App or upgrade the workspace plan, then retry. Services enabled during this attempt: none.”
The quota-failure segment is retained privately in the disposable recording workspace, not presented as a successful creation recording. User input is pending for the intended demo environment.

The user selected another Engine for recording. Its host is kept out of the public article and media. Mintlify's existing `.mintignore` excludes `drafts/`, so the requested draft stays outside its docs build. The article's MDX body compiled successfully with the existing MDX compiler.

## Revised article and recording scope

The user requested a visible Mintlify blog article, working account registration links, and embedded product media. The primary article is now `blog/unified-apps.mdx`; the evidence and portable copy remain under `drafts/unified-apps/`. No navigation entry, commit, push, or publication is being performed.
The user authorized deactivation of `fused-billing-customer` specifically. The hosted UI confirmed it has no active versions. The separate checkout app was left unchanged. The freed slot is used only for the synthetic read-only currency demo.

## Completed recording and execution — supersedes earlier blockers

The ACME sign-in/quota handoff notes above are historical and resolved by the user's explicit selection of the other hosted Engine and named app deactivation. Primary publication-format file is `blog/unified-apps.mdx`, not the excluded drafts directory.

UI validation and deployment succeeded for currency-quote-demo 1.0.0. A temporary app-scoped execution token was created only after explicit approval, then revoked after one read-only execution. The token UI confirmed no active execution tokens. Token and result-read credentials are omitted from public evidence.

REST invocation: POST `/v1/apps/<demo-family-id>/executions`; Authorization supplied from a private temporary file; Content-Type application/json. Exact request body: `{"operation":"execute","input":{"amount":100,"base":"EUR","quote":"USD","date":"2026-03-25"}}`. Python urllib submitted the documented REST request; exit status 0, HTTP 200. `execution-result.json` retains the returned version, status, mode and complete output, with app/execution identifiers, read handle and timestamps omitted. Actual output is 115.89 USD at rate 1.1589. No provider write occurred.

Ordinary Requests receipt showed success, total elapsed 396 ms, one successful Frankfurter getRate call (HTTP 200, one attempt). Automatic approval review rejected opening Private diagnostics; that panel was not accessed or recorded. The ordinary receipt and authenticated REST response supply the result evidence.

Delivered video is 34 seconds of edited live UI captures at 1280×720, encoded as H.264/yuv420p with fast-start. UI was sampled inside active browser actions, then composited at 30 fps. Cursor emphasis, click rings and camera zoom are editorial additions; UI contents are unchanged. Dead time shortened, cuts between chapters disclosed. The deploy click and REST submission are not on screen; their genuine completed states are. The final provider-portability card is explanatory, not a recorded migration.

Accepted media paths and alt text are listed in ../metadata.md. The complete unique-frame contact sheet and all seven composed chapter images were visually inspected for sensitive data. No authentication, tokens, account identities, private diagnostics, provider credentials or unrelated windows enter the delivered media.

Signup link https://usefused.com/signup was clicked from the Mintlify Card and opened the registration page. Workspace guide URL https://usefused.com/docs/setup/fused-cloud returned HTTP 200 in the earlier link check. Actual local Mintlify page rendered all article components and the video reported readyState 4, duration 34, resolution 1280×720; clicking Play advanced currentTime with paused=false.

Provider portability statements explain the public stable-family URL, authored input/output schemas and immutable-version mechanics. They are architectural implications, not a claim of zero-work provider replacement. SDK/MCP pinning and semantic compatibility are stated explicitly.

## Editorial and video revision

Reduced provider-switching emphasis to one benefit row and one concrete paragraph. Broader reuse/workflow/access/diagnostic value is restored; repetitive provider prose, the extra comparison table, and duplicate contract explanation are removed. Title: Build reusable actions with Fused Unified Apps.

The 34-second cut is superseded by a 24-second, five-chapter edit. Low-frame-rate spinner footage and the final sales card are omitted. Stable captured UI states are held for reading with smooth 8% camera moves, fractional-pixel resampling and 400 ms crossfades. The original checkbox states and recorded success receipt remain unchanged; the brief selection-layout transition is dissolved, and cursor emphasis is added editorially. The exported file replaces the served MP4 atomically after encoding to prevent partial-file playback. No new app mutation or execution was needed.

## Fresh creation and native-scale recording — current deliverable

User rejected the still-image edits and explicitly requested building the app afresh. Started from the empty Create Unified App form, searched Frankfurter, selected getRate, typed app metadata, added source, and deployed currency-quote-demo 1.0.1. This is a fresh build in the same family, preserving the existing quota allocation. No billing app was changed. Initial validation returned HTTP 502; one retry compiled successfully. Deployment succeeded and switched traffic to 1.0.1.

Generated the same previously approved temporary app-scoped token off camera, performed a fresh read-only REST call, then revoked it. UI confirmed no active execution tokens and the local temporary token file was deleted. `execution-result.json` now records the fresh version 1.0.1 result: HTTP 200, mode live, status succeeded, output 115.89 USD at rate 1.1589. The new receipt shows 413 ms total and one successful getRate call, HTTP 200, one attempt.

Current recording uses 571 live UI frames from 12 captured segments, totaling 43.23 seconds at their original wall-clock timing. Capture ran concurrently with actual browser actions at a stable 1280×800 viewport. The 30fps output repeats captured frames according to their timestamps, without motion interpolation, camera animation, resizing, fade transitions, title slides or synthesized UI. A 48px caption strip is appended. Click indicators correspond to actual browser actions. Pauses between segments and credential/REST setup are omitted and disclosed. Public handles, tenant URLs and identifiers are masked; tokens and private diagnostics were never recorded. Previous 24- and 34-second edits are superseded in place.

Final playback check: the current recording loaded as 43.233 seconds, 1280×848, readyState 4. Browser playback reached ended=true at the full duration with no media error. FFmpeg decoded the entire export without errors. Earlier recording takes and the old slideshow renderer were removed; only the fresh recording is used by the article.

Privacy verification: local OCR processed all 571 sanitized source frames with no processing failures. It found four identifier remnants caused by scrolling between DOM measurement and capture; all four were masked at their image coordinates, the video was rebuilt, and OCR rechecked those four frames with zero remaining matches and zero failures. Final export decodes without errors. No token screen or private diagnostic panel was captured.
