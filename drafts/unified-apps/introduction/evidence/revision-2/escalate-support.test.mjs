import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import { z } from 'zod';

const source = readFileSync(process.env.APP_SOURCE, 'utf8');
const executable = stripTypeScriptTypes(source)
  .replace(/^import .*;\n/gm, '')
  .replace('export default buildUnifiedApp(', 'return buildUnifiedApp(');
// Inject provider doubles into the actual article source, without changing its logic.
const createApp = new Function('z', 'buildUnifiedApp', 'services', executable);
const input = { caseId: 'SUP-42', title: 'Export fails', details: 'A large export times out.', requesterEmail: 'ada@example.com' };

// Capture provider calls so failure cases can prove that no extra issue is created.
function harness({ issueError, emailError, email = { id: 'email-test' } } = {}) {
  const calls = [];
  const services = {
    '@martins-joseph/gitlab': {
      // Return a fixture, never reach the real issue tracker.
      async postApiV4ProjectsIdIssues(params) {
        calls.push({ operation: 'issue', params });
        // Model a failure before a usable issue response is available.
        if (issueError) throw issueError;
        return { id: 42, web_url: 'https://gitlab.com/example/support/-/issues/7' };
      },
    },
    resend: {
      // Return a fixture or transport failure without sending an email.
      async postEmails(params) {
        calls.push({ operation: 'email', params });
        // Model a notification failure after the issue already exists.
        if (emailError) throw emailError;
        return email;
      },
    },
  };
  // Retain the declared schemas and execute method for the isolated test boundary.
  const buildUnifiedApp = (definition) => definition;
  const app = createApp(z, buildUnifiedApp, services);
  // Mirror the documented input/execute/output boundary for this local logic test.
  const run = async (value) => app.output.parse(await app.execute({ input: app.input.parse(value) }));
  return { run, calls };
}

// Invalid email must fail before creating an issue or sending a notification.
test('rejects invalid email before provider calls', async () => {
  const h = harness();
  await assert.rejects(h.run({ ...input, requesterEmail: 'not-an-email' }));
  assert.equal(h.calls.length, 0);
});

// Blank case identifiers must not create untraceable escalation records.
test('rejects whitespace case ID before provider calls', async () => {
  const h = harness();
  await assert.rejects(h.run({ ...input, caseId: '   ' }));
  assert.equal(h.calls.length, 0);
});

// A provider failure cannot be presented as a successful escalation.
test('issue failure prevents notification', async () => {
  const h = harness({ issueError: new Error('issue service unavailable') });
  await assert.rejects(h.run(input), /issue service unavailable/);
  assert.equal(h.calls.length, 1);
});

// The successful path proves the fixed destination and issue-derived notification key.
test('creates one issue and confirms one notification', async () => {
  const h = harness();
  const result = await h.run(input);
  assert.equal(result.notification, 'accepted');
  assert.equal(result.issueId, '42');
  assert.equal(h.calls.length, 2);
  assert.equal(h.calls[0].params.id, '123');
  assert.equal(h.calls[1].params['Idempotency-Key'], 'support-escalation-issue-42');
});

// A notification transport error must preserve the already-created issue.
test('returns the issue when notification throws', async () => {
  const h = harness({ emailError: new Error('timeout') });
  const result = await h.run(input);
  assert.equal(result.notification, 'needs_attention');
  assert.equal(result.issueId, '42');
  assert.equal(h.calls.length, 2);
});

// HTTP-shaped success without a message ID remains an unconfirmed notification.
test('missing email ID reports needs_attention', async () => {
  const h = harness({ email: {} });
  const result = await h.run(input);
  assert.equal(result.notification, 'needs_attention');
  assert.equal(result.issueId, '42');
  assert.equal(h.calls.length, 2);
});
