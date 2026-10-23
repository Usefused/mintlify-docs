# Editorial metadata

Title: Building a billing support brief that doesn’t bluff
Description: Design a Fused Unified App that keeps billing API failures, empty results, and incomplete pages distinct.
Audience: backend and platform engineers building support consoles and agent actions.
Tags: engineering, integrations, TypeScript, reliability, Fused, Stripe.
Status: saved to the existing Margin draft; unpublished. Engineering slug: `billing-support-brief`. The introductory article is a separate draft under `unified-apps`.
Format: approximately 1,275 words including code and tables; one architecture diagram, narrow code excerpts, synthetic failure output, and a failure-case table.

## Files

- `post.md`: portable canonical article.
- `margin.md`: Margin rendering with its native Diagram block.
- `examples/`: complete TypeScript source, YAML, local test harness and pinned dependency manifest.
- `evidence/manifest.md`: findings and execution outcomes recorded during the work.
- `margin.json`: saved draft identity and revision.

## Validation and limits

15 local contract tests passed using Node 24.21.0 and Zod 4.6.7. Fused CLI 0.42.2 plan compiled the same source and accepted the two selected operations. No app deployment, execution token generation, live Stripe request, or live credential test was performed. Synthetic output is explicitly labeled. No latency or production-performance claim is made.

The sample is a bounded support view, not an exhaustive ledger or authorization policy. The backend must authorize the caller and resolve the tenant’s customer ID. Credentials belong in the selected Fused bucket. The example uses this workspace’s `stripe` service reference and pinned version; other workspaces may use a qualified reference.

## Publication tasks

Review the draft before publishing. Test provider execution with an authorized Stripe test-mode account before describing it as an end-to-end deployment. Recheck service version availability near publication. The old currency article and media remain untouched; no unrelated demo media is used here.

Review image: `assets/margin-preview.png` — alt text: “Margin preview of the billing support engineering article, showing its opening and unpublished draft status.” Review evidence only; not embedded in the publishable article.

## Complete-code update

The article now includes the exact compiled TypeScript and YAML in native Margin tabs, plus separate plan and apply commands. The portable Markdown includes both complete files as ordinary fenced blocks. No one-click Engine import link was found in public documentation. Copy buttons are not available in the current Margin code-block renderer; application-change scope was raised separately. Terminal commands remain text rather than screenshots so readers can select and reuse them.

Review image: `assets/margin-code-tabs.png` — alt text: “Margin draft showing TypeScript, YAML, and Create the app tabs with the sample configuration.” Not an article illustration.

Post separation: engineering content preserved exactly under its existing post ID. Original introductory content restored as a separate unpublished Margin draft; see `../margin.json`. User selected article-only scope, so Copy buttons and Margin renderer changes are excluded.
