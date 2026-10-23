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
