# Introducing Unified Apps: one capability, every caller

A customer reports a broken export. Your product needs to raise an engineering issue. So does the support console. Then an agent joins the party. Three callers, three implementations, and three interpretations of “escalated”.

**Unified Apps turn that integration into a shared capability.** The product asks to escalate a case. The app owns the provider calls, credentials, validation, and failure handling. Teams reuse the organisation’s implementation instead of reconstructing it from a wiki page.

Let’s build `escalate-support`: create a GitLab issue, notify the engineering team by email, and return a useful result even if the notification fails.

## Lightweight where it counts

A Unified App is an Engine-hosted TypeScript action with an input schema, an output schema, and a YAML file selecting its operations and credentials.

You could build a microservice for this. You would also need to host its process, expose an authenticated endpoint, wire provider secrets, and build the SDK or agent-facing interface you want teams to use. With a configured Fused Engine, those surfaces are already provided. You supply the action and its config; Fused [compiles and hosts it](https://usefused.com/docs/app/unified-apps/write-code).

That is “lightweight” in deployment and maintenance: no separate HTTP server or container to ship for each action. It is not a claim of zero infrastructure or unlimited runtime. Your team still owns the business rules, tests, and rollout.

## Start with the outcome

With the [CLI installed and signed in](https://usefused.com/docs/quickstart), describe the capability. Replace project `123` with an appropriate GitLab test project:

```bash
fused-cli describe --name escalate-support --bucket default \
  "Escalate a support case using GitLab and Resend. \
   Accept caseId, title, details and requesterEmail; validate the email. \
   Create an issue in GitLab project 123 with the case ID and requester details. \
   Email its link to delivered@resend.dev from Fused <onboarding@resend.dev>. \
   Use the issue ID as the notification idempotency key. \
   Return issueId, issueUrl and notification: accepted or needs_attention. \
   Preserve the issue result if notification fails; never recreate it in that call."
```

Under the hood, `describe`:

- Finds services in your workspace, then the Registry when needed.
- Selects concrete versions and operations, and drafts code against their contracts.
- Shows the source and configuration for review.
- After confirmation, activates missing services, deploys the app, and saves its files locally.

You do not need a separate service-installation command or another `app apply` after accepting the proposal. Normal permissions still apply. [Describe’s workflow](https://usefused.com/docs/app/from-a-prompt) includes an interactive review; deployment itself does not create an issue or send an email.

## The implementation is yours

Here is a reviewed implementation of that goal and its matching config. The project and notification recipient belong to the owning team, so callers cannot choose arbitrary destinations. The recipient below is Resend’s test address; use your team’s address and a verified sender for real notifications.

### escalate-support.ts

```typescript
import { z } from "zod";
import { buildUnifiedApp } from "@fused/unified-app";
import { services } from "@fused/operations";

// Set the owning team's project once, rather than asking every caller to route it.
const PROJECT_ID = "123";

export default buildUnifiedApp({
  // Reject malformed requests before either provider receives a call.
  input: z.object({
    caseId: z.string().trim().min(1).max(100),
    title: z.string().trim().min(1).max(150),
    details: z.string().max(10000),
    requesterEmail: z.string().email(),
  }),
  // Keep every caller on the same result contract, including partial completion.
  output: z.object({
    issueId: z.string(),
    issueUrl: z.string().url(),
    notification: z.enum(["accepted", "needs_attention"]),
  }),
  // Preserve a created issue even when its notification needs separate recovery.
  async execute({ input }) {
    const rawIssue = await services["@martins-joseph/gitlab"].postApiV4ProjectsIdIssues({
      id: PROJECT_ID,
      title: `${input.caseId}: ${input.title}`,
      description: `Requester: ${input.requesterEmail}\n\n${input.details}`,
    });
    // Validate the provider result before exposing identifiers or notifying anyone.
    const issue = z.object({ id: z.number().int(), web_url: z.string().url() }).parse(rawIssue);
    const issueId = String(issue.id);

    // A notification is unconfirmed until the provider returns a valid message ID.
    let notification: "accepted" | "needs_attention" = "needs_attention";
    // Isolate notification failure from the issue that already exists.
    try {
      const sent = await services.resend.postEmails({
        "Idempotency-Key": `support-escalation-issue-${issueId}`,
        from: "Fused <onboarding@resend.dev>",
        to: "delivered@resend.dev",
        subject: `Support escalation: ${input.caseId}`,
        text: `An engineering issue needs attention:\n${issue.web_url}`,
      });
      // HTTP success alone is insufficient if the provider omits its message ID.
      z.object({ id: z.string().min(1) }).parse(sent);
      // Mark acceptance only after validating the provider acknowledgement.
      notification = "accepted";
    } catch {
      // Keep needs_attention; recreating the issue would make recovery worse.
    }
    return { issueId, issueUrl: issue.web_url, notification };
  },
});
```

### escalate-support.yaml

```yaml
apiVersion: fused/v1
kind: unified_app
name: escalate-support
version: "1.0.0"
bucket: default
source_path: escalate-support.ts
services:
  "@martins-joseph/gitlab":
    version: "v4"
    operations: [postApiV4ProjectsIdIssues]
    auth:
      type: api_key
      name: access_token_header
  resend:
    version: "1.5.0"
    operations: [postEmails]
    auth:
      type: bearer
      name: bearerAuth
```

The app rejects invalid email addresses before either provider runs. If issue creation fails, notification never starts. If the email fails or returns no message ID, the result still includes the issue and `notification: "needs_attention"`. “Issue created; notification unconfirmed” is considerably more useful than “something went wrong”.

This is not a transaction across two providers. Do not retry the whole action blindly: that could create another issue. The notification uses an issue-derived key, which [Resend retains for 24 hours](https://resend.com/docs/dashboard/emails/idempotency-keys); reuse it with the same email payload when retrying that step. Cross-caller duplicate suppression needs a durable `caseId → issueId` record with concurrency control. The owning team should add that policy before enabling automatic whole-action retries.

## Credentials stay behind the capability

If the `default` bucket already has the credentials, skip setup. Otherwise, these commands prompt for secrets without echoing them:

```bash
fused-cli bucket credential set @martins-joseph/gitlab \
  --bucket default --type api_key --auth-name access_token_header
fused-cli bucket credential set resend \
  --bucket default --type bearer --auth-name bearerAuth
```

`--auth-name` is the security-scheme name declared by the service’s API contract, not a nickname you invent. For another provider, inspect `fused-cli service show <service> --registry --json`, or omit the selection flags and let the credential command prompt for a supported method.

The YAML explicitly selects GitLab’s header credential because this catalogue version also allows anonymous requests. Fused resolves the chosen credentials from `bucket: default` and adds them at dispatch. No provider key enters the source or caller payload. Credential writes take effect immediately; the [bucket guide](https://usefused.com/docs/bucket/store-credentials) covers rotation and CI stdin input.

## Three callers, one implementation

After deployment, save the app family ID and the execution token shown once. The product can call the family endpoint; set `FUSED_ENGINE_URL`, `FUSED_APP_FAMILY_ID`, and `FUSED_APP_TOKEN` from your workspace and deployment:

```bash
curl -X POST "$FUSED_ENGINE_URL/v1/apps/$FUSED_APP_FAMILY_ID/executions" \
  -H "Authorization: Bearer $FUSED_APP_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"operation":"execute","input":{"caseId":"SUP-42","title":"Export fails","details":"Large exports time out.","requesterEmail":"ada@example.com"}}'
```

For the admin tool and agent, [attach the deployed app to an SDK or MCP consumer](https://usefused.com/docs/app/unified-apps/use-from-apps) with this config fragment, then deploy that consumer:

```yaml
unified_apps:
  escalate_support:
    name: escalate-support
    version: "1.0.0"
```

The admin tool uses its generated SDK client, configured with the Engine HTTP `engineUrl` and the **consumer’s** execution token:

```typescript
const result = await sdk.unifiedApps.escalate_support({
  caseId: "SUP-42", title: "Export fails",
  details: "Large exports time out.", requesterEmail: "ada@example.com",
});
```

The agent uses the MCP server’s `execute` tool:

```json
{
  "name": "execute",
  "arguments": {
    "operation": "unified_app:escalate_support",
    "input": {
      "caseId": "SUP-42", "title": "Export fails",
      "details": "Large exports time out.", "requesterEmail": "ada@example.com"
    }
  }
}
```

These are alternative callers for the same case, not three commands to execute in sequence. Check the execution’s `status` before reading `output`, then inspect `output.notification`. A succeeded execution can intentionally report an unconfirmed notification. Queued or running REST executions need a [result lookup](https://usefused.com/docs/app/unified-apps/results-and-debugging).

## Swap providers deliberately

Move from GitLab to another tracker by changing the app’s implementation, selected operations, and credentials. Preserve the input, output, and behaviour callers rely on, including existing issue identifiers and failure semantics. Product code can keep calling the same capability.

The rollout matters. **Direct REST calls to the family URL use the active version.** After a deployment or promotion changes that active version, subsequent calls use the new implementation without a caller-side URL change. Test the replacement before switching traffic; “stable URL” does not mean “unchanging behaviour”.

**SDK/MCP attachments pin an exact version and do not silently follow.** Their selected version must still be receiving traffic. Coordinate a new consumer version when switching the Unified App, or affected calls can fail. A Unified App’s direct hosted MCP family endpoint follows active traffic instead; existing sessions must reconnect. The [versioning guide](https://usefused.com/docs/app/unified-apps/versions) covers promotion and rollback.

The result is an organisational capability: one team maintains how escalation works, while product teams and agents use it. The next caller needs a contract, not a crash course in your issue tracker.

> [Create a Fused account](https://usefused.com/signup) to get started. If you already have an account, [build your first Unified App](https://usefused.com/docs/app/unified-apps): connect the CLI to your workspace and describe the capability you want.
