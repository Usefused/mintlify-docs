# Evidence ledger

Access date: 2026-10-16.

## Editorial research

- https://blog.cloudflare.com/cdnjs-dev-platform-migration/ — problem-led narrative, architecture, partial-success failure modes, tradeoffs. Editorial reference only; no Cloudflare outcomes are attributed to this example.
- https://blog.cloudflare.com/project-crossbow-lessons-from-refactoring-a-large-scale-internal-tool/ — purpose-built support tooling and design choices tied to actual users. Editorial reference only.

## Public Fused sources

- https://usefused.com/docs/app/unified-apps — downloaded public Markdown to unified-apps.md; supports TypeScript/YAML configuration, exact selected operations, plan/apply, execution envelope.
- https://github.com/Usefused/cli/releases/tag/v0.42.2 — installed release identity. Executable resolved outside source checkout, version 0.42.2.

## Discovery

Released CLI in a disposable directory returned no Registry search matches for osv, github, npm. Workspace metadata confirms Stripe service version 2026-07-29.dahlia is enabled. Private workspace identifiers were not saved into article evidence. No customer data queried.

## Contract discovery, recorded before implementation

- https://docs.stripe.com/api/subscriptions/list — default omits canceled subscriptions; `status=all` includes every status; accepts customer and limit (1–100).
- https://docs.stripe.com/api/invoices/list — customer and status filtering, newest-created ordering.
- https://docs.stripe.com/api/pagination — `has_more` and `starting_after` describe the boundary of a page.
- https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json — public provider contract, current branch; not substituted for the pinned Fused service schema.
- Released CLI workspace metadata exposed the historical shorthand `stripe`, but operation lookup required catalog-qualified `@martins-joseph/stripe`. The selected pinned version exposes `GetSubscriptions` (GET /v1/subscriptions) and `GetInvoices` (GET /v1/invoices). No mutation operation is selected.

Design decision: return one bounded page from each list with an explicit `hasMore` flag. The brief is a support view, not an exhaustive account ledger. Do not aggregate amounts across currencies or equate `open` with overdue or a failed payment.

## Implementation checkpoint

- Created `examples/billing-brief.ts` and `examples/billing-brief.yaml` using the public Fused two-file interface and exact catalog operations.
- Provider-page parsing checks the requested customer on every record; response projection excludes contact details, metadata, hosted invoice URLs, and payment details.
- The two independent reads run concurrently. Provider rejections become explicit `upstream_error`; invalid pages become `invalid_response`. Projection/programming errors are not swallowed by the provider-error catch.
- `coverage=complete` requires both reads to succeed with no additional pages; `partial` covers one failed section or truncated data; `unavailable` means neither section can supply trusted records.
- Source and real Zod schemas loaded successfully under Node 24.21.0. Only hosted Fused module bindings are mocked for local tests; no provider data or credentials are used.

## Test checkpoint — before hosted compilation

Command: `node --import ./fused-test-loader.mjs --test billing-brief.test.mjs`
Context: disposable directory, Node v24.21.0, npm-installed Zod 4; original TypeScript source with only Fused hosting bindings substituted.
Result: exit 0, 15 tests passed, 0 failed. Raw output: `tests-first-run.txt`.
Coverage: successful empty data, scoped bounded requests, both independent partial-failure paths, total outage, pagination, missing envelope fields, inconsistent continuation, oversize pages, wrong-customer records, wrong invoice status, data minimization, invalid input before I/O, mixed currencies, deterministic proof of concurrent reads.
No live Stripe requests or performance benchmarks were performed. Test durations are harness timings, not Fused or provider latency.

## Plan checkpoint

`fused-cli app plan -f billing-brief.yaml --no-input --json` rejected catalog-qualified service reference with `config_service_unresolved`. No compilation or deployment occurred. Trying the historical enabled workspace reference `stripe`, keeping YAML and TypeScript references identical. This is compatibility discovery, not a claim that every workspace uses that spelling.

## Compile result and synthetic example

The enabled workspace reference `stripe` succeeded. `fused-cli app plan -f billing-brief.yaml --no-input --json` completed with exit 0 and created a plan selecting only `GetInvoices` and `GetSubscriptions`. Public documentation states plan checks and compiles the linked TypeScript. Receipt: `plan.json`, with private endpoint and resource identifiers removed. No apply, execution token issuance, or provider request was performed.

Final source uses `stripe` consistently in YAML and TypeScript. Discovery used `@martins-joseph/stripe`; readers must use the service reference enabled in their own workspace. This compatibility finding stays in the evidence ledger rather than dominating the article.

Runtime: Node 24.21.0, Zod 4.6.7, Fused CLI 0.42.2. The same TypeScript core is used by local tests and hosted plan. `capture-example.mjs` executed with synthetic provider responses and produced `partial-result.json` (exit 0). The article must label this as a synthetic failure example, not a live Stripe response.

## Editorial checkpoint

Reorganized the accumulated findings into the final problem-led narrative: false empty-account result, typed uncertainty, bounded reads, independent failures, failure-case table, and Fused's narrow operation boundary. Approximately 1,275 words including code and tables. Light humor is original; Cloudflare articles supplied structural inspiration, not copied language or claims.

The article's JSON was parsed and compared exactly with `partial-result.json`. The Margin rendering uses one supported Diagram tag; portable Markdown retains a Mermaid fence. No old currency-demo media remains in the rewrite.

## Margin checkpoint

Replaced existing draft through `margin push` using the reviewed revision guard; title updated to “Building a billing support brief that doesn’t bluff.” The response confirmed `status: draft`, and saved content matched `margin.md` exactly. Identity and new revision recorded in `margin.json`. Browser preview confirms the revised title, article, code blocks, tables, and unpublished state. Old currency draft sources remain intact.

## Visual review

Margin preview loaded the architecture diagram successfully with all five nodes and edges. Inspected the opening, code/table structure, and draft state. `assets/margin-preview.png` shows the opening and unpublished status; the account reminder was dismissed before capture, with no image editing. This screenshot is review evidence, not an article illustration.

Final local checks: article JSON matches captured synthetic output; Markdown fences and Margin diagram delimiters balance; no unfinished TODO or temporary workspace paths in article prose; original Markdown and MDX drafts still exist; `git diff --check` passes for tracked changes.

## Reader code handoff

User requested complete code, copy buttons, and an optional one-click Engine creation shortcut. Added the exact plan-compiled `billing-brief.ts` and `billing-brief.yaml` to the article, with native Margin tabs separating source, config, and creation commands. No implementation changes were made. Plan and apply are separate instructions; no apply was executed. Test credentials and authorized customer mapping are called out at the point of use.

Inspected Margin’s rendered code DOM and built-in Markdown guide: ordinary fenced blocks currently render as `pre > code`, without native Copy buttons. The embedded authoring skill documents tabs but no custom button or executable-HTML facility. Asked whether expanding scope to Margin’s renderer is desired; no nonfunctional Copy control was inserted.

Read the public Fused docs index and searched public documentation for a prefilled Unified App import/template link. None was found. Omitted the optional one-click shortcut; documented plan/apply is the working creation route. Terminal screenshots add no evidence here beyond the existing logs and would make commands harder to copy, so command blocks are used.

Saved the complete-code update with the reviewed Margin revision. Response content equals the local Margin source and status remains draft. Source/YAML excerpts are identical to the compiled files; only article content changed, so no redundant application test run was necessary.

Preview verification: TypeScript, YAML, and Create the app tabs render and switch correctly. The rendered TypeScript was compared exactly with `examples/billing-brief.ts` (match). The creation tab displays both commands and the synthetic customer input correctly. `assets/margin-code-tabs.png` is the reviewed screenshot of the new code section, with no account details exposed. The draft remains unpublished. Copy-button implementation is pending the user's scope choice.

## Separate-post restoration

Read current Margin list and engineering revision. Confirmed the current body exactly matched the saved engineering source. Changed only the engineering slug to `billing-support-brief` with the reviewed revision guard; response body remained identical and status draft. Created the introduction from the preserved original `../margin.md` with its original title and slug `unified-apps`; response matched source exactly and status draft. Saved both post identities in their respective `margin.json` files. No publication occurred. The prior Copy-button scope question was resolved by the user: article changes only.
