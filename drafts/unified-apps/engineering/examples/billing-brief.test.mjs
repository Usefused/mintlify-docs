import test from 'node:test';
import assert from 'node:assert/strict';
import { buildBrief, PAGE_LIMIT } from './billing-brief.ts';

const customerId = 'cus_demo';
const input = { customerId };
const subscription = { id: 'sub_demo', customer: customerId, status: 'canceled', cancel_at_period_end: false };
const invoice = { id: 'in_demo', customer: customerId, status: 'open', currency: 'usd', amount_remaining: 4500, due_date: null };
// Model only documented provider envelope fields, with explicit pagination state.
const page = (data = [], has_more = false) => ({ object: 'list', data, has_more });
// Provide successful readers by default; each test overrides the behavior it challenges.
const reads = (subscriptions = page(), invoices = page()) => ({
  // Resolve fixtures without contacting a provider or requiring credentials.
  subscriptions: async () => subscriptions,
  // Keep invoice fixtures independently controllable for partial-failure tests.
  invoices: async () => invoices,
});
// Represent a provider rejection without leaking its diagnostic text into public output.
const fail = async () => { throw new Error('private upstream diagnostic'); };

// Prove that an empty account requires two successful, complete observations.
test('successful empty pages are complete evidence', async () => {
  const result = await buildBrief(input, reads());
  assert.equal(result.coverage, 'complete');
  assert.deepEqual(result.openInvoices, { state: 'ready', items: [], hasMore: false });
});
// Capture the intended customer filter, all-status history, and fixed page budget.
test('provider requests are scoped and bounded', async () => {
  const calls = [];
  const result = await buildBrief(input, {
    // Retain request arguments so filtering errors cannot hide behind fixture success.
    subscriptions: async (query) => { calls.push(query); return page([subscription]); },
    // Capture the invoice state independently of the subscription filter.
    invoices: async (query) => { calls.push(query); return page([invoice]); },
  });
  assert.deepEqual(calls, [
    { customer: customerId, status: 'all', limit: 20 },
    { customer: customerId, status: 'open', limit: 20 },
  ]);
  assert.equal(result.subscriptions.items[0].status, 'canceled');
});
// A failure must not erase useful evidence from the other section.
test('invoice failure preserves subscription history', async () => {
  const result = await buildBrief(input, { ...reads(page([subscription])), invoices: fail });
  assert.equal(result.coverage, 'partial');
  assert.equal(result.subscriptions.items[0].id, 'sub_demo');
  assert.deepEqual(result.openInvoices, { state: 'unavailable', reason: 'upstream_error' });
  assert.equal(JSON.stringify(result).includes('private'), false);
});
// Check the symmetric failure path rather than assuming both adapters behave alike.
test('subscription failure preserves open invoices', async () => {
  const result = await buildBrief(input, { ...reads(page(), page([invoice])), subscriptions: fail });
  assert.equal(result.coverage, 'partial');
  assert.equal(result.openInvoices.items[0].amountRemaining, 4500);
});
// Two failed reads cannot yield a successful empty account.
test('two failures produce unavailable coverage', async () => {
  assert.equal((await buildBrief(input, { subscriptions: fail, invoices: fail })).coverage, 'unavailable');
});
// A valid but incomplete page must not be advertised as the full account history.
test('additional pages make coverage partial', async () => {
  const result = await buildBrief(input, reads(page([subscription], true), page([invoice])));
  assert.equal(result.coverage, 'partial');
  assert.equal(result.subscriptions.hasMore, true);
});
// Missing pagination evidence must fail closed instead of defaulting to false.
test('missing has_more invalidates a page', async () => {
  const result = await buildBrief(input, reads({ object: 'list', data: [] }));
  assert.deepEqual(result.subscriptions, { state: 'unavailable', reason: 'invalid_response' });
});
// An impossible continuation should not be presented as usable provider evidence.
test('empty page with continuation is invalid', async () => {
  assert.equal((await buildBrief(input, reads(page([], true)))).subscriptions.state, 'unavailable');
});
// Bound normalization work and output size even when a provider ignores the limit.
test('oversized provider pages are rejected', async () => {
  const result = await buildBrief(input, reads(page(Array(PAGE_LIMIT + 1).fill(subscription))));
  assert.equal(result.subscriptions.state, 'unavailable');
});
// A valid response for a different customer is still invalid for this request.
test('cross-customer records never reach the caller', async () => {
  const result = await buildBrief(input, reads(page([{ ...subscription, customer: 'cus_other' }])));
  assert.equal(result.subscriptions.state, 'unavailable');
  assert.equal(JSON.stringify(result).includes('cus_other'), false);
});
// Avoid treating a wrong invoice filter as evidence about open invoices.
test('non-open invoices invalidate the invoice section', async () => {
  const result = await buildBrief(input, reads(page(), page([{ ...invoice, status: 'paid' }])));
  assert.equal(result.openInvoices.state, 'unavailable');
});
// A narrow projection keeps incidental provider data out of agent and UI consumers.
test('projection drops contact data and preserves nullable due dates', async () => {
  const result = await buildBrief(input, reads(page(), page([{ ...invoice, customer_email: 'synthetic@example.test', metadata: { internal: 'omit' } }])));
  assert.deepEqual(result.openInvoices.items, [{ id: 'in_demo', currency: 'usd', amountRemaining: 4500, dueAt: null }]);
  assert.equal(JSON.stringify(result).includes('synthetic'), false);
});
// No request can run if caller validation fails before the parallel reads.
test('blank customer input triggers zero provider calls', async () => {
  let count = 0;
  // Count accidental provider access rather than relying only on the thrown error.
  const unexpected = async () => { count += 1; return page(); };
  await assert.rejects(buildBrief({ customerId: '' }, { subscriptions: unexpected, invoices: unexpected }));
  assert.equal(count, 0);
});
// Keep monetary evidence per invoice; cross-currency sums would invent a conversion policy.
test('mixed currencies retain their own amounts', async () => {
  const result = await buildBrief(input, reads(page(), page([invoice, { ...invoice, id: 'in_eur', currency: 'eur', amount_remaining: 3000 }])));
  assert.deepEqual(result.openInvoices.items.map(
    // Compare currency/amount pairs without aggregating unlike units.
    item => [item.currency, item.amountRemaining]), [['usd', 4500], ['eur', 3000]]);
});
// Verify both reads start before either result is needed, without timing-sensitive assertions.
test('independent reads start concurrently', async () => {
  let release;
  const pending = new Promise(
    // Allow the invoice reader to unblock the subscription reader deterministically.
    resolve => { release = resolve; });
  const result = await buildBrief(input, {
    // Wait for the other operation to prove that execution is not serialized.
    subscriptions: async () => { await pending; return page(); },
    // Release the first operation after the second has actually started.
    invoices: async () => { release(); return page(); },
  });
  assert.equal(result.coverage, 'complete');
});
