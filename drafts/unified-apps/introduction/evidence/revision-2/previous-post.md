# Introducing Unified Apps: give your integration a home

A welcome email starts as six lines in your signup handler. Then the admin tool needs it. Then an agent needs it. Now you have three implementations, two subject lines, and a surprisingly lively discussion about which one is correct.

**Unified Apps separate your integration from your product.** Your product calls a capability—“welcome this member”—while the app owns the provider calls, credentials, and implementation. Write that action in TypeScript, give it an input and output contract, and let Fused host it.

That separation matters when you change providers. Keep the app’s contract and expected behavior stable, and you can replace the service behind it without rewriting every product that calls it. The provider changes. Your signup flow keeps asking for the same thing.

Our example accepts a name and email address, sends a welcome message through Resend, and returns its message ID. Small enough to read before your coffee changes temperature.

## An action with a contract

A Unified App has two files. TypeScript defines the input, provider calls, and output. YAML selects the service versions and operations the app can use, and the bucket that supplies their credentials.

For `welcome-member`, that boundary looks like this:

```text
{ email, displayName }
        → welcome-member
        → Resend: postEmails
        → { messageId }
```

The caller supplies the recipient. The app owns the sender and message. Fused resolves the provider credential when it dispatches the request. The caller never needs the Resend key.

An action can coordinate several providers. We’ll start with one.

For an organisation, the same boundary turns integrations into capabilities teams can use. The team that owns customer communications can maintain `welcome-member`: the approved sender, message, provider, and error handling. Product teams call it instead of each reimplementing the organisation’s email rules.

You distribute a capability, not a wiki page everyone must remember to follow.

## Describe the outcome

With the [CLI installed and signed in to your workspace](https://usefused.com/docs/quickstart), run this in an interactive terminal. This example uses the existing `default` bucket; you need permission to create apps, activate any missing services, and use that bucket.

```bash
fused-cli describe --name welcome-member --bucket default \
  "Create a Unified App using Resend postEmails. \
   Accept email and displayName as strings. \
   Send a plain-text welcome email from Fused <onboarding@resend.dev>, \
   subject Welcome aboard, text welcoming displayName. \
   Return messageId as a string from the provider response id. \
   Use only postEmails. Keep credentials in the default bucket, never in source. \
   Add a concise explanatory comment to the execute function and any validation or decision logic."
```

That one command handles the setup under the hood:

- **Find the services:** check your workspace first, then search the Registry when needed.
- **Select the operations:** resolve concrete service versions and the operations required for your goal.
- **Draft the app:** generate TypeScript against those operation contracts and prepare the matching configuration.
- **Apply after your review:** activate missing services through the normal workspace activation flow, deploy the app, and save its files locally.

You don’t need to run a separate `service add`, write the YAML first, or follow up with `app apply` after accepting the proposal. The CLI handles that work, with the usual permission checks and an interactive confirmation before applying changes.

The proposal for this example selected:

```text
resend@1.5.0: postEmails
```

Review the input, selected operations, and returned value, then confirm to deploy. Save the returned app family ID and execution token, which is shown once. Deployment registers the action; it does not send an email. [Describe uses Fused’s configured models](https://usefused.com/docs/app/from-a-prompt), with no additional model API key required.

## Here are the files

These are the files behind the action: generated logic with comments tidied up, and its matching YAML. You don’t have to type them out after running `describe`; they show what you can inspect and maintain. Generated wording may vary. If you prefer to author the files yourself, follow the [manual plan/apply workflow](https://usefused.com/docs/app/unified-apps/write-code).

### welcome-member.ts

```typescript
import { z } from "zod";
import { buildUnifiedApp } from "@fused/unified-app";
import { fused } from "@fused/operations";

const sendEmailResponseSchema = z.object({
  id: z.string().optional(),
});

export default buildUnifiedApp({
  input: z.object({
    email: z.string(),
    displayName: z.string(),
  }),
  output: z.object({
    messageId: z.string(),
  }),
  // Send one welcome email using the credential resolved by the Engine.
  async execute({ input }) {
    const response = await fused.resend.postEmails({
      from: "Fused <onboarding@resend.dev>",
      to: input.email,
      subject: "Welcome aboard",
      text: `Welcome aboard, ${input.displayName}!`,
    });

    // Validate the provider result before exposing the app’s smaller output contract.
    const parsedResponse = sendEmailResponseSchema.parse(response);

    // The contract permits an omitted id, but a messageId cannot be returned without it.
    if (parsedResponse.id === undefined) {
      throw new Error("Resend response did not include an email id");
    }

    return {
      messageId: parsedResponse.id,
    };
  },
});
```

### welcome-member.yaml

```yaml
apiVersion: fused/v1
kind: unified_app
name: welcome-member
version: "1.0.0"
bucket: default
source_path: welcome-member.ts
services:
  resend:
    version: "1.5.0"
    operations: [postEmails]
```

The YAML selects **one operation**, `postEmails`, and pins its service version. Keep the service reference identical in the code and config; use the exact reference enabled in your workspace.

The TypeScript exposes a smaller contract than the provider API. Callers send two fields and receive one. It also checks the response: Resend's selected contract permits an omitted `id`, but this app promises a `messageId`. A missing ID becomes an error instead of a successful-looking response with a hole in it.

The sender above is for testing. [Resend's email API guide](https://resend.com/docs/api-reference/emails/send-email) shows the test sender and recipient used here; configure a verified sending domain before welcoming actual users. Accepting a message is also different from delivering it to an inbox.

## Supply the credential once

`describe` can find and enable Resend. It cannot invent your Resend API key. If the selected bucket already has the credential, skip this step. Otherwise, store it before the first call:

```bash
fused-cli bucket credential set resend \
  --bucket default --type bearer --auth-name bearerAuth
```

The CLI prompts for the secret without echoing it. You need permission to manage credentials. This writes the credential immediately; no additional apply is needed.

The app’s `bucket: default` setting tells Fused where to resolve the Resend credential. Fused adds provider authentication server-side at dispatch. No key in the source, YAML, or prompt. Your integration’s most valuable string gets to stay out of Git.

Run the same command with a replacement key to rotate it for subsequent requests. For CI, the [bucket guide](https://usefused.com/docs/bucket/store-credentials) shows how to supply credentials through stdin.

## Call the capability

Set `FUSED_ENGINE_URL` to your workspace’s HTTP address, and `FUSED_APP_FAMILY_ID` and `FUSED_APP_TOKEN` from the deployment. Then make a test request:

```bash
curl -X POST "$FUSED_ENGINE_URL/v1/apps/$FUSED_APP_FAMILY_ID/executions" \
  -H "Authorization: Bearer $FUSED_APP_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"operation":"execute","input":{"email":"delivered@resend.dev","displayName":"Ada"}}'
```

That bearer token authorizes the Fused app. The bucket holds the separate Resend credential. A completed successful execution returns the app's `messageId` inside `output`; a queued or running execution needs a [result lookup](https://usefused.com/docs/app/unified-apps/results-and-debugging). An HTTP acceptance response alone does not mean the email was sent.

## Change the provider, keep the capability

Suppose you move away from Resend. Replace the selected service in the YAML and its call in the TypeScript. Configure the new provider’s credential in the bucket, then map its response back to the same `{ messageId }` output.

Your product still sends `{ email, displayName }` to `welcome-member`. It doesn’t need the new provider’s SDK, key, or response format. That is the useful boundary: integration changes stay with the integration.

Preserving the field names is only part of the job. The new implementation must preserve the behavior callers rely on, including what counts as success and how failures are reported. Test that contract, then deploy a [new immutable version](https://usefused.com/docs/app/unified-apps/versions). The family REST address stays stable. SDK and MCP consumers select explicit versions, so those consumers need a deliberate version update.

## Give teams something they can use

Your signup flow can call the action over HTTP. An SDK or MCP app can [select the Unified App as a dependency](https://usefused.com/docs/app/unified-apps/use-from-apps), so application code and agents can use the same implementation.

The owning team maintains the integration. Other teams get a capability with a defined contract, rather than instructions for rebuilding it correctly. The same pattern works for creating a customer, opening a support case, or provisioning an account.

Fused hosts the action and supplies its selected credentials. You decide what the action means. And when the provider changes, “welcome this member” can stay exactly that.

> If you already have a Fused account, [get started with your first Unified App](https://usefused.com/docs/app/unified-apps). Connect the CLI to your workspace, describe the capability you want, and review the generated app.
