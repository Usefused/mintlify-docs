A customer asks why their subscription stopped working. Support needs two things: the subscription history and the open invoices. That sounds like two API calls and a small amount of glue code.

Then the invoice request times out, the glue returns `[]`, and the tool confidently reports that there are no open invoices.

An API timeout has just been promoted to an accounting fact.

Let's build a billing support brief that avoids that mistake. It is a small Fused Unified App: one customer ID in, two independently readable sections out. A support console or agent can use the same action without each inventing its own interpretation of a failed request.

## Make uncertainty part of the response

The useful unit of output is a section with a state. A successful read contains records and a pagination flag. An unsuccessful read contains a reason. It does **not** contain an empty array dressed as good news.

```typescript
type Section<T> =
  | { state: "ready"; items: T[]; hasMore: boolean }
  | {
      state: "unavailable";
      reason: "upstream_error" | "invalid_response";
    };
```

This makes the consuming code ask the right question first: *do we have evidence?* Only then should it count records.

The brief also reports overall coverage:

| Coverage | Meaning |
| --- | --- |
| `complete` | Both reads succeeded and neither reports another page. |
| `partial` | At least one section is usable, but a read failed or more records exist. |
| `unavailable` | Neither section can supply trusted records. |

Here, “complete” means complete for these two queries. It says nothing about refunds, disputes, or whether a customer should retain access. Two successful reads are also not an atomic snapshot: billing can change between them.

## Two reads, two chances to be honest

The action selects two Stripe operations: list subscriptions and list invoices. They share a customer ID but neither depends on the other's result, so they run concurrently.

[Diagram width="full" height="300"]
flowchart LR
  Caller[Authorized backend or agent] --> Brief[Billing support brief]
  Brief --> Subscriptions[Subscription history]
  Brief --> Invoices[Open invoices]
  Subscriptions --> Result[Ready or unavailable per section]
  Invoices --> Result
[/Diagram]

There is a detail worth catching before writing the wrapper. Stripe's subscription list excludes canceled subscriptions by default. For a support investigation, the canceled subscription may be the entire point. We explicitly request `status: "all"`. [Stripe documents that filter here](https://docs.stripe.com/api/subscriptions/list).

The requests are deliberately small:

```typescript
// Include canceled history while keeping this read scoped to one customer.
const subscriptionQuery = { customer: customerId, status: "all", limit: 20 };
// Open is an invoice state; it does not by itself mean overdue or payment failed.
const invoiceQuery = { customer: customerId, status: "open", limit: 20 };
```

The invoice section uses Stripe's [customer and status filters](https://docs.stripe.com/api/invoices/list). It returns identifiers, currency, remaining amount, and due date. The subscription section returns identifiers, statuses, and whether cancellation is scheduled for period end.

No customer email, address, payment details, or provider metadata comes along for the ride. A support brief should be brief in what it exposes, too.

## Twenty records is a budget, not a claim of completeness

A support action should not turn into an unbounded account-history export. Each operation requests one page of at most 20 records.

Stripe's [`has_more` field](https://docs.stripe.com/api/pagination) survives the transformation as `hasMore`. When it is true, coverage is `partial` even if both requests succeeded. The UI can show the available records and direct the operator to the full billing view.

There is no “total outstanding balance” in this response. We may not have every invoice, and adding amounts in different currencies produces a number with excellent confidence and no useful meaning. Amounts stay attached to their invoice and currency, in the provider's units.

The implementation also rejects oversized pages, missing pagination fields, and records belonging to a different customer. A valid JSON document can still be the wrong answer.

## Catch the outage, keep the useful half

The dangerous shortcut looks like this:

```typescript
// Incorrect: provider failure becomes indistinguishable from a successful empty read.
const invoices = await listInvoices().catch(() => []);
```

Instead, each section catches its own provider rejection and returns `unavailable`. The other section can still succeed. Response validation happens after that catch; our own projection bugs should not acquire an “upstream outage” disguise.

Here is the result of a synthetic failure case: subscription history arrives, but the invoice reader rejects. This is output from the example's local contract harness, not a live customer record.

```json
{
  "customerId": "cus_demo",
  "coverage": "partial",
  "subscriptions": {
    "state": "ready",
    "items": [
      {
        "id": "sub_demo",
        "status": "canceled",
        "cancelAtPeriodEnd": false
      }
    ],
    "hasMore": false
  },
  "openInvoices": {
    "state": "unavailable",
    "reason": "upstream_error"
  }
}
```

Support can see the cancellation and knows invoice data is missing. An agent has the same boundary: it can describe the subscription, but it has no basis for saying the customer owes nothing.

Raw upstream errors are excluded from the brief. Operators need diagnostics; customers and downstream agents do not need whatever happened to be in an exception message.

## Test the places where the answer can lie

The example has 15 passing local contract tests using synthetic provider responses. The important cases are behavioral:

| Input or failure | Required behavior |
| --- | --- |
| Two successful empty pages | `complete`, with two ready, empty sections. |
| One provider read rejects | `partial`; retain the other section. |
| Both reads reject | `unavailable`, with no invented records. |
| A page reports more records | `partial`, with `hasMore: true`. |
| Missing pagination or wrong-customer data | Reject the affected section as `invalid_response`. |
| Blank customer ID | Reject before either provider call starts. |
| Mixed currencies | Preserve each invoice amount; do not sum them. |

The suite also checks that both reads start independently and that contact data is stripped. These tests establish the response contract. They do not measure provider latency or prove a live credential setup.

## Give the action a narrow operating envelope

Fused hosts the TypeScript and routes its selected provider operations. The sample's configuration allows exactly the two reads:

```yaml
apiVersion: fused/v1
kind: unified_app
name: billing-support-brief
version: "1.0.0"
bucket: default
source_path: billing-brief.ts
services:
  stripe:
    version: "2026-07-29.dahlia"
    # Looking up billing context must not grant payment or subscription mutation access.
    operations: [GetSubscriptions, GetInvoices]
```

Use the service reference and version enabled in your workspace, consistently in both YAML and TypeScript. Credentials belong in the configured bucket. The [Unified App authoring guide](https://usefused.com/docs/app/unified-apps/write-code) describes the two-file contract and the plan/apply workflow.

The app validates input before launching the reads, validates the provider pages, then projects them into the output schema. Fused validates the authored output before returning it. That last boundary catches an implementation that drifts from its advertised contract.

There are still two statuses to inspect. Fused's execution `status` tells you whether the action completed. The brief's `coverage` tells you how much billing evidence it obtained. An execution can succeed while returning `coverage: "unavailable"`. Consumers must check both; [an accepted, pending execution is not a completed result either](https://usefused.com/docs/app/unified-apps/results-and-debugging).

Before invocation, the calling backend must authorize the operator and resolve the customer ID from the appropriate tenant. Checking that an ID starts with `cus_` is input validation, not permission to inspect that customer. Keep the execution token on that trusted boundary.

The result is a useful action with a modest job: collect billing context and say exactly how much of it is available. It does not collect a payment, change a subscription, or make an access decision.

Those are separate actions. They deserve more than a hopeful `catch` block.

## Build it in your Engine

The full implementation is below. Save the files as `billing-brief.ts` and `billing-brief.yaml`; the filenames matter because the YAML links to the TypeScript. Start with a Stripe test-mode credential and test customer.

[Tabs title="The complete app" variant="boxed"]
[Tab title="TypeScript"]

### billing-brief.ts

```typescript
import * as z from "zod/mini";
import { buildUnifiedApp } from "@fused/unified-app";
import { services } from "@fused/operations";

export const PAGE_LIMIT = 20;
// Reject blank or malformed identifiers before a missing filter can broaden a read.
export const inputSchema = z.object({
  customerId: z.string().check(z.regex(/^cus_[A-Za-z0-9]+$/)),
});
const subscriptionItem = z.object({
  id: z.string(), status: z.string(), cancelAtPeriodEnd: z.boolean(),
});
const invoiceItem = z.object({
  id: z.string(), currency: z.string(),
  amountRemaining: z.number().check(z.int(), z.gte(0)),
  dueAt: z.nullable(z.number().check(z.int(), z.gte(0))),
});
const unavailableSchema = z.object({
  state: z.literal("unavailable"),
  reason: z.enum(["upstream_error", "invalid_response"]),
});

// Make successful observations and failed reads impossible to confuse in the output.
function sectionSchema<T extends z.ZodMiniType>(item: T) {
  return z.discriminatedUnion("state", [
    z.object({
      state: z.literal("ready"), items: z.array(item), hasMore: z.boolean(),
    }),
    unavailableSchema,
  ]);
}
export const outputSchema = z.object({
  customerId: z.string(),
  coverage: z.enum(["complete", "partial", "unavailable"]),
  subscriptions: sectionSchema(subscriptionItem),
  openInvoices: sectionSchema(invoiceItem),
});

type Unavailable = z.infer<typeof unavailableSchema>;
type Section<T> = { state: "ready"; items: T[]; hasMore: boolean } | Unavailable;
type Query = { customer: string; status: "all" | "open"; limit: number };
export type Reader = (query: Query) => Promise<unknown>;

// Treat malformed pages as unavailable instead of presenting untrusted account facts.
async function readSection<T extends z.ZodMiniType, U>(
  read: () => Promise<unknown>, itemSchema: T,
  project: (item: z.infer<T>) => U,
): Promise<Section<U>> {
  let raw: unknown;
  try {
    raw = await read();
  // Provider failures are a known partial-result case; raw errors stay out of the brief.
  } catch {
    return { state: "unavailable", reason: "upstream_error" };
  }
  // Limit and validate the provider page before mapping or disclosing any records.
  const page = z.safeParse(z.object({
    object: z.literal("list"),
    data: z.array(itemSchema).check(z.maxLength(PAGE_LIMIT)),
    has_more: z.boolean(),
  }), raw);
  // Missing fields must never silently become an empty, apparently successful list.
  if (!page.success) {
    return { state: "unavailable", reason: "invalid_response" };
  }
  // A continuation without a record is inconsistent with this first-page contract.
  if (page.data.has_more && page.data.data.length === 0) {
    return { state: "unavailable", reason: "invalid_response" };
  }
  return {
    state: "ready", items: page.data.data.map(project),
    hasMore: page.data.has_more,
  };
}

// Read independent sections concurrently while retaining each section's evidence boundary.
export async function buildBrief(
  rawInput: unknown, reads: { subscriptions: Reader; invoices: Reader },
) {
  // Validate before launching either call so no unfiltered request can be issued.
  const { customerId } = z.parse(inputSchema, rawInput);
  const [subscriptions, openInvoices] = await Promise.all([
    readSection(
      // Include canceled history and constrain the provider read to this customer.
      () => reads.subscriptions({ customer: customerId, status: "all", limit: PAGE_LIMIT }),
      z.object({
        id: z.string(), customer: z.literal(customerId), status: z.string(),
        cancel_at_period_end: z.boolean(),
      }),
      // Expose only the support fields, not the provider's full customer record.
      (item) => ({ id: item.id, status: item.status, cancelAtPeriodEnd: item.cancel_at_period_end }),
    ),
    readSection(
      // Open invoices are useful context without implying that they are overdue.
      () => reads.invoices({ customer: customerId, status: "open", limit: PAGE_LIMIT }),
      z.object({
        id: z.string(), customer: z.literal(customerId), status: z.literal("open"),
        currency: z.string().check(z.regex(/^[a-z]{3}$/)),
        amount_remaining: z.number().check(z.int(), z.gte(0)),
        due_date: z.nullable(z.number().check(z.int(), z.gte(0))),
      }),
      // Preserve provider units and null due dates without inventing business meaning.
      (item) => ({ id: item.id, currency: item.currency,
        amountRemaining: item.amount_remaining, dueAt: item.due_date }),
    ),
  ]);
  let coverage: "complete" | "partial" | "unavailable" = "partial";
  // Complete means both bounded reads succeeded and neither reports unseen records.
  if (subscriptions.state === "ready" && openInvoices.state === "ready"
      && !subscriptions.hasMore && !openInvoices.hasMore) {
    coverage = "complete";
  // A total provider outage still returns a useful, explicit domain outcome.
  } else if (subscriptions.state === "unavailable" && openInvoices.state === "unavailable") {
    coverage = "unavailable";
  }
  // Validate the public contract separately from the provider response contract.
  return z.parse(outputSchema, { customerId, coverage, subscriptions, openInvoices });
}

export default buildUnifiedApp({
  input: inputSchema,
  output: outputSchema,
  // Route only the two selected read operations through Fused's credential boundary.
  async execute({ input }) {
    return buildBrief(input, {
      // Keep service-specific request syntax at the provider adapter boundary.
      subscriptions: (query) => services["stripe"].GetSubscriptions(query),
      // Share the same scope and bounds for the independently readable invoice section.
      invoices: (query) => services["stripe"].GetInvoices(query),
    });
  },
});
```

[/Tab]
[Tab title="YAML"]

### billing-brief.yaml

```yaml
apiVersion: fused/v1
kind: unified_app
name: billing-support-brief
version: "1.0.0"
bucket: default
source_path: billing-brief.ts
services:
  "stripe":
    version: "2026-07-29.dahlia"
    # The support action must not be able to change subscriptions or collect payments.
    operations: [GetSubscriptions, GetInvoices]
```

[/Tab]
[Tab title="Create the app"]

Save both files in the same directory. Before planning, enable the selected Stripe version in your workspace and [store a suitable Stripe credential in the configured bucket](https://usefused.com/docs/bucket/store-credentials). Use your workspace’s service reference consistently in both files.

Review the proposed app:

```bash
fused-cli app plan -f billing-brief.yaml --no-input --json
```

When the plan matches what you intend to deploy, create the hosted app:

```bash
fused-cli app apply -f billing-brief.yaml
```

Deployment creates the action; it does not query a customer. Save the returned app family ID and execution token securely. Follow the [invocation guide](https://usefused.com/docs/app/unified-apps#create-your-first-app) to call it with a customer ID your backend has authorized:

```json
{"customerId":"cus_demo"}
```

`cus_demo` is a synthetic example. Replace it with an authorized test customer for a provider-backed run.

[/Tab]
[/Tabs]
