import { writeFileSync } from 'node:fs';
import { buildBrief } from './billing-brief.ts';
const output = await buildBrief({ customerId: 'cus_demo' }, {
  // Supply canceled-history evidence from a documented provider-shaped synthetic response.
  subscriptions: async () => ({ object: 'list', has_more: false, data: [
    { id: 'sub_demo', customer: 'cus_demo', status: 'canceled', cancel_at_period_end: false },
  ] }),
  // Exercise a provider failure without contacting Stripe or exposing diagnostics.
  invoices: async () => { throw new Error('Synthetic upstream failure'); },
});
writeFileSync('partial-result.json', JSON.stringify(output, null, 2) + '\n');
console.log(JSON.stringify(output, null, 2));
