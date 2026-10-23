# Editorial metadata

Status: unpublished local draft. No commit, push, navigation entry, or publication.
Primary Mintlify page: `../../blog/unified-apps.mdx`.
Portable Markdown: `post.md`; `article.mdx` is a synchronized MDX copy.
Live local review: http://localhost:3001/blog/unified-apps (Mintlify preview).
The older custom preview.html is superseded by the real Mintlify preview.

Title: Build reusable actions with Fused Unified Apps
Description: Host integration logic once and reuse it across products and agents.
Audience: developers who know APIs and TypeScript but are new to Unified Apps.
Tags: APIs, integrations, TypeScript, developer tools, provider portability.
Slug: unified-apps

## Demonstrated coverage

- User-authorized deactivation of the specifically selected billing app freed one slot. The other billing app was not changed.
- Created and compiled currency-quote-demo 1.0.1 in the hosted Engine UI, then deployed it.
- Generated an explicitly approved execution token for this app only, with a one-day expiry; revoked it immediately after the read-only test. UI confirmed no active execution tokens.
- Invoked the stable family execution URL with synthetic data: 100 EUR to USD, date 2026-03-25. HTTP 200, status succeeded, rate 1.1589, convertedAmount 115.89.
- Opened its ordinary Requests receipt: success, total 413 ms, getRate HTTP 200, one attempt. Private diagnostics were not opened.
- Verified embedded video metadata and browser playback, and clicked the signup card to confirm it opens the actual registration page.
- CLI version/help and service discovery were run with released CLI 0.41.1. CLI plan/apply and SDK/MCP attachment snippets are public-documentation-based reader instructions, not separately executed deployments.
- A second-provider migration is an architectural example, not a demonstrated migration. The article states compatibility and pinned-consumer requirements.

## Media inventory

Paths are relative to the Mintlify repository root.

- `videos/unified-apps/create-and-use.mp4`: 43.23 seconds, 1280×848, H.264/yuv420p, fast-start, silent. Fresh screen capture during real UI actions at native 1280×800, with a 48px caption strip. No zoom, reframing, slide cards or image transitions. Actual typing, selection, scrolling, compile, deploy and receipt inspection are shown. Click indicators use the actual control coordinates and event times. Pauses between tool interactions and off-camera credential/REST steps are omitted. Successful compilation required one retry after a gateway 502; failed footage is not included in the public edit.
- `videos/unified-apps/captions.vtt`: English captions, also readable as burned-in text in the video.
- `images/blog/unified-apps/video-poster.jpg`: full-page service search from the new recording.
- `images/blog/unified-apps/workflow-code.jpg`: real editor crop; alt: typed currency quote input and output.
- `images/blog/unified-apps/ready-to-deploy.jpg`: real validated plan; alt: selected Frankfurter operation and separate deploy action.
- `images/blog/unified-apps/execution-success.jpg`: real receipt; alt: successful currency quote execution and runtime phases.

Privacy: account identity, host address, app IDs, tokens, read handles, and unrelated windows are excluded from delivered media. Credential setup was excluded from capture; identifying UI labels are masked in the delivered recording. Recorded frames and a 36-frame contact sheet were inspected. OCR checked all 571 source frames; four moving-label remnants were corrected and rechecked successfully. Identifying labels are masked without changing the product interaction. Sensitive temporary token/response files are excluded from the repository and removed after testing.

## Before publishing

Review the article and media; refresh public product behavior and service availability if publication is delayed. Add the page to the desired blog/navigation only when publication is authorized. Upload all referenced images/video/captions together. The demo app remains deployed for review and has no active execution token.

## Margin restoration

The original introduction has been restored as its own unpublished Margin draft under slug `unified-apps`. `margin.md` is the restored body; `margin.json` contains its new ID and editor URL. The engineering case study remains a separate draft under `billing-support-brief`; see `engineering/margin.json`.

## CLI-focused introduction rewrite — 2026-10-16

Current Margin introduction source is introduction/margin.md; portable source is introduction/post.md. Earlier parent-directory post.md, article.mdx, and margin.md remain preserved. Rewrite introduces provider decoupling and shared organisational capabilities, then shows a generated welcome-member action, its YAML, bucket credentials, plan/apply, and a test call. No screenshots. Engineering draft remains separate and unchanged.
