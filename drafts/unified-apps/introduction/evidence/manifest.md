# Introduction rewrite evidence

Date: 2026-10-16. Target: introduction draft e85b71c4-b33d-476a-bda8-3ac510675a1b, slug unified-apps. Engineering draft is separate and will not be edited.

## Editorial direction

Use the problem/design/implications structure from the previously reviewed Cloudflare engineering posts, with concise prose and original light humor. This article introduces Unified Apps, rather than repeating the billing support case study.

- https://blog.cloudflare.com/cdnjs-dev-platform-migration/ — editorial structure reference.
- https://blog.cloudflare.com/project-crossbow-lessons-from-refactoring-a-large-scale-internal-tool/ — editorial structure reference.

## Public product contracts

- https://usefused.com/docs/app/from-a-prompt — describe resolves operations, drafts source, requires interactive confirmation, and deploys separately from execution. Saved as from-a-prompt.md.
- https://usefused.com/docs/app/unified-apps — hosted action model, files, plan/apply and execution envelope. Saved as overview.md.
- https://usefused.com/docs/app/unified-apps/versions — immutable versions and stable family REST URL. Saved as versions.md.
- https://usefused.com/docs/app/unified-apps/use-from-apps — explicit SDK/MCP version selection and hosted action reuse. Saved as consumers.md.
- Released CLI 0.42.2: `fused-cli describe --help` exit 0. Saved describe-help.txt. Confirms default Unified App, --name, --bucket, --version, --kind, and interactive review. A newer release notification does not change the installed version used here.

## Scope

Describe and apply snippets will be sourced reader instructions, not claimed successful runs. No email sending or deployed-app mutation is authorized or required for this editorial request. Read-only operation discovery and non-applying plan are in scope. Provider output will not be invented.

## CLI and bucket focus

User requested no screenshots: final article and handoff will contain text/code only. Added bucket setup to the narrative before describe. Consulted fused-bucket instructions and public store-credentials documentation; no credential values were read or modified.

Resend 1.5.0 exposes `postEmails`, POST /emails, with JSON from/to/subject/text and a provider message ID. The exact catalog schema is saved as resend-schema.json, with unnecessary catalog row IDs removed. https://resend.com/docs/api-reference/emails/send-email supports sender/recipient/message semantics. The example will use a test sender and explicit test recipient, not real users.

## Describe proposal, 2026-10-16

Ran installed fused-cli 0.42.2 from /private/tmp/fused-intro-demo in an interactive terminal. The welcome-member goal selected resend@1.5.0 postEmails and produced source saved in describe-proposal.txt. Declined the apply confirmation with n; command exited 1 with “describe initialization cancelled”. No deployment or email execution occurred. The article source preserves the generated logic; explanatory comments were adjusted, and the matching YAML was assembled from the public config contract.

## Non-applying plan

fused-cli app plan -f welcome-member.yaml --no-input --json, run from /private/tmp/fused-intro-demo, exited 0. Sanitized receipt saved as plan.json: removed Engine URL, plan ID and permission resource IDs. Plan selected only Resend 1.5.0 postEmails with bearerAuth and required bucket.use on default. No apply or provider execution.

CLI bucket credential set flags, service add flags and login/config behavior checked against released CLI help and public docs. Credential writes, service activation, apply and curl execution remain reader instructions; they were not executed for this article.

## Product positioning refinement

User clarified the primary value: detach integrations from products, replace providers behind a capability contract, and offer organisation-owned implementations to teams. Revised the lead and closing sections around this benefit. Qualified provider replacement: preserve input/output and behavioral contract; REST family address remains stable while SDK/MCP version selections need deliberate updates. No claim that an arbitrary provider switch is automatically behavior-compatible or requires no rollout.

## Margin verification

Margin push used reviewed revision guards. Readback matched margin.md exactly and retained draft status. Engineering post 4272d6d3-9bce-444b-86a0-8a441b704f6e retained revision 192cb4ce-642e-4a30-a539-044bd99f0b8b and identical content.

## Describe-first correction — 2026-10-16

Rechecked https://usefused.com/docs/app/from-a-prompt.md. Public docs explicitly say discovery checks workspace then Registry, missing services go through activation before app apply, and confirmation precedes application. Removed manual service activation, bucket inspection, sign-in, CI and duplicate plan/apply command blocks from the primary walkthrough. Added an explicit four-step under-the-hood explanation. Kept provider credential setup conditional on a missing bucket credential and placed it before first execution. Full code/config remain explanatory output, not required manual input. No new app or provider operations were run.

Simplified Margin draft saved with revision guard, read back, and matched local margin.md exactly. Status remains draft. Revision: 48b2f04d-3b8a-4df3-9b18-e85f1c231475.

## Existing-account closing note — 2026-10-16

User requested a closing invitation for existing account holders. Read current post: externally published since prior edit, body unchanged. Added only a closing note linking the verified public Unified Apps guide. Revision-guarded push preserved published status; readback matches local content. Revision 37eedfbc-0f07-4168-81de-e820bdaee549.

## Editorial revision 2 — 2026-10-16

Feedback: demonstrate SDK/MCP reuse, clarify active REST version routing, explain auth scheme names, validate email, address duplicate side effects, add signup CTA, remove repetition, use UK spelling, and provide dedicated metadata/share image. Investigating a multi-step example with partial-failure handling; no provider calls authorised for this evidence pass. Public versions/consumers/write-code docs re-fetched and stored under revision-2. Lightweight means an Engine-hosted action with two authored files and shared runtime/auth/delivery surfaces, not an unmeasured latency or resource claim.

## Revision 2 sources and metadata

https://usefused.com/docs/app/unified-apps/versions — REST family calls follow active traffic, direct MCP sessions reconnect after traffic changes. https://usefused.com/docs/app/unified-apps/use-from-apps — SDK/MCP attachment shapes, exact version selection, consumer tokens, active-version requirement. https://usefused.com/docs/app/unified-apps/write-code — two authored files, Engine compilation/hosting, input and output validation. https://resend.com/docs/dashboard/emails/idempotency-keys — provider email key retention is 24 hours, same request/key returns prior response. Public homepage links to /signup.

Linear catalogue has no auth config and describe failed with operation discovery catalogue is invalid. No activation occurred. GitLab catalogue has PRIVATE-TOKEN auth scheme access_token_header; considering explicit auth selection because its operation declares an anonymous alternative. User chose support escalation. Preserve the smaller original example under examples/welcome-member.*.

Social asset assets/unified-apps-social.png generated and visually inspected. Uploaded through Margin SEO/sharing UI. Dedicated description has 145 characters. Live HTML verified description, og:image and twitter:card=summary_large_image. No renderer changes.

## Support escalation evidence

Released CLI describe generated GitLab/Resend source and a workspace activation plan for GitLab v4. Declined apply (n); no services enabled, issues created or emails sent. Saved the generated proposal. Reviewed source simplifies the result handling, fixes the project in the app, bounds inputs, validates URLs, and explicitly selects GitLab PRIVATE-TOKEN auth access_token_header and Resend bearerAuth. Non-applying plan stopped at config_service_unresolved because GitLab remains disabled; do not claim a deployed or end-to-end-validated app. Six local tests ran against the article source with provider doubles: invalid email, blank case ID, issue failure, full acceptance, notification exception, missing email ID. All passed. Notification idempotency does not prevent duplicate issue creation across whole-app retries.

Revision 2 saved to the existing published introduction with a reviewed revision guard. CLI readback matches margin.md. Live HTML contains the escalation source/caller examples and large-image metadata. Final revision ae0ec5e3-df2e-4e44-9478-f96446d29450. Engineering article was not edited.

## GitHub replacement — 2026-10-17

User requested GitHub instead of GitLab. Registry search currently returns no GitHub service. Consulted official GitHub REST issue documentation and public github/rest-api-description OpenAPI: owner/repo path parameters, title/body request fields, id/html_url response, API version 2026-03-10, and Issues write permission. Prepared a minimal explicit bearer-auth contract named createIssue. Read-only import plan accepted one added endpoint (create_service); no import apply, activation, deployment, issue creation or email send occurred. Article includes optional import setup and explains actual service references must match the reader’s proposal. Code, config, credential commands, examples and prose now use GitHub.

Six local tests passed against the GitHub source with provider doubles; results saved in github/test-results.txt. No end-to-end provider execution claimed. Margin CLI revision-guarded push succeeded; readback matches margin.md exactly, status remains published, SEO is unchanged, and public HTML contains GitHub/createIssue and large-image sharing metadata. Verified revision: 9c32c3ae-97b5-4b2a-af33-d6a056ecc135. Engineering article was not edited.

## Editorial reset — 2026-10-17

User rejected the overexplained introduction. Rewrite around reusable team-owned capabilities, provider independence and a short describe-first example. Remove microservice comparison, defensive qualifications and repeated thesis. Preserve working source/config and essential credential, version-routing and retry semantics. Previous body preserved in editorial-reset/before.md. No new runtime claims or provider calls.

## User-supplied replacement — 2026-10-18

Replaced the introduction title and body with the supplied publish-release article, without editorial changes. Moved the initial H1 into Margin’s title field. Preserved the supplied file and previous body in user-replacement-2026-10-18/. Revision-guarded CLI push succeeded; readback exactly matches the supplied body and title. Published status and unified-apps slug retained; public HTML verified. Revision 5d463cd0-ae13-425b-8db9-63075fbfd5db. No example commands or code from the replacement were executed; verification covered content transfer only.
