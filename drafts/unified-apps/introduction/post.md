# Introducing Unified Apps: multi-step integrations you can rewire without touching the caller

Most integrations aren't a single API call. They're a process.

Publishing a release is a good example. You find the last release, collect everything merged since then, write the release notes, create the release on GitHub, and announce it to your users. That's four calls across two services, in an order that matters, with rules in between: don't publish the same tag twice, don't announce a release that doesn't exist, don't silently drop changes past the first page of results.

Today, that process usually ends up in one of two places. Either it's hard-coded into an application, which couples your product to every provider it touches, or it's handed to an AI agent along with a set of API tools, and the agent works out the steps again on every run.

Today we're introducing **Unified Apps**. A Unified App is a deterministic, multi-step process that you write once in TypeScript and Fused hosts for you. Callers send a typed input and get a typed output. Everything in between is yours: the order of the steps, the rules, the providers and the credentials. Because callers depend only on the contract, you can replace a provider inside the app, ship it as a new version, and your callers' code doesn't change.

The same app can be called by your developers through a generated SDK and by your agents as a tool on an MCP server.

## What is a Unified App?

A Unified App turns a sequence of provider operations into one action with a contract you define.

```text
                    publish-release  (hosted on the Fused Engine)
                  ┌────────────────────────────────────────────────┐
 { repository,    │ 1. GitHub   list releases     → previous tag   │    { releaseUrl,
   tag }      ───▶│ 2. GitHub   search merged PRs → changes        │───▶  pullRequests,
                  │ 3. code     build release notes                │      announcementId }
                  │ 4. GitHub   create release                     │
                  │ 5. Resend   email the announcement             │
                  └────────────────────────────────────────────────┘
```

Each app has two files:

- **A TypeScript file** that declares the input schema, the output schema, and an `execute` function containing the steps.
- **A YAML file** that pins each provider's service version, lists the exact operations the app is allowed to call, and points at the bucket that holds the credentials.

On every call, Fused validates the input, runs `execute` on the Engine, validates the output, and returns it. Provider credentials are added server-side when each call is dispatched, so they never appear in the app's source or in the caller's environment.

The process runs the same way every time. It doesn't depend on which caller started it, and it doesn't depend on how a model happened to plan it on that run.

## Building `publish-release`

We'll build the release process end to end. Given a repository and a tag, the app will:

1. Refuse to continue if the tag has already been released, and otherwise find the previous release.
2. Find every pull request merged into `main` since that release.
3. Group the pull requests into release notes.
4. Create the GitHub release.
5. Email the announcement and return a provider-neutral announcement ID.

### Describe it

With the [Fused CLI installed and signed in](https://usefused.com/docs/quickstart), you can describe the process in plain language:

```bash
fused-cli describe --name publish-release --bucket default \
  "Create a Unified App that publishes a GitHub release and announces it by email.
   Accept repository (owner/repo) and tag (vMAJOR.MINOR.PATCH).
   List the repository's releases; fail if the tag already exists, otherwise use the latest published release as the base.
   Search for pull requests merged into main since that release; fail if there are none.
   Build release notes grouped into Features, Fixes and Other using the feature and fix labels.
   Create the release on main with those notes.
   Then email the notes to releases@acme.dev with Resend.
   Return releaseUrl, pullRequests (count) and announcementId.
   Keep credentials in the default bucket."
```

`describe` looks for GitHub and Resend in your workspace, searches the Registry for any that aren't enabled, selects the operations the process needs, and drafts TypeScript against those operations' contracts. It shows you a proposal containing the services, their pinned versions, the operations and the source. Nothing is applied until you confirm. Once you do, it activates any missing services, deploys the app, and saves the files under `.fused/unified_app/` so you can maintain them like any other code. If you'd rather write the files yourself, the [plan and apply workflow](https://usefused.com/docs/app/unified-apps/write-code) produces the same result.

### The code

```typescript
// .fused/unified_app/publish-release.ts
import { z } from "zod";
import { buildUnifiedApp } from "@fused/unified-app";
import { fused } from "@fused/operations";

// Only the provider fields this app relies on.
const releaseList = z.array(
  z.object({ tag_name: z.string(), draft: z.boolean(), published_at: z.string().nullable() }),
);
const mergedPRs = z.object({
  total_count: z.number(),
  items: z.array(
    z.object({ number: z.number(), title: z.string(), labels: z.array(z.object({ name: z.string() })) }),
  ),
});
type PullRequest = z.infer<typeof mergedPRs>["items"][number];

export default buildUnifiedApp({
  input: z.object({
    repository: z.string().regex(/^[\w.-]+\/[\w.-]+$/), // "acme/web"
    tag: z.string().regex(/^v\d+\.\d+\.\d+$/),           // "v2.4.0"
  }),
  output: z.object({
    releaseUrl: z.string().url(),
    pullRequests: z.number(),
    announcementId: z.string(),
  }),

  async execute({ input }) {
    const [owner, repo] = input.repository.split("/");

    // 1. Never publish the same tag twice; otherwise start from the last published release.
    const releases = releaseList.parse(await fused.github.reposListReleases({ owner, repo, per_page: 20 }));
    if (releases.some((r) => r.tag_name === input.tag)) {
      throw new Error(`${input.tag} has already been released`);
    }
    const previous = releases.find((r) => !r.draft && r.published_at !== null);
    const since = previous?.published_at ?? "1970-01-01T00:00:00Z";

    // 2. Everything merged into main since then. Fail loudly rather than publish partial notes.
    const prs = mergedPRs.parse(
      await fused.github.searchIssuesAndPullRequests({
        q: `repo:${input.repository} is:pr is:merged base:main merged:>${since}`,
        per_page: 100,
      }),
    );
    if (prs.total_count === 0) throw new Error(`Nothing merged since ${previous?.tag_name ?? "the first commit"}`);
    if (prs.total_count > prs.items.length) throw new Error("More than 100 pull requests; split the release");

    // 3. Same notes format for every release.
    const notes = releaseNotes(prs.items, previous?.tag_name);

    // 4. Create the release.
    const release = z.object({ html_url: z.string() }).parse(
      await fused.github.reposCreateRelease({
        owner, repo, tag_name: input.tag, target_commitish: "main", name: input.tag, body: notes,
      }),
    );

    // 5. Announce it only once the release exists.
    const announcementId = await announce(input.repository, input.tag, release.html_url, notes);

    return { releaseUrl: release.html_url, pullRequests: prs.total_count, announcementId };
  },
});

// The only part of the app that knows how announcements are delivered.
async function announce(repository: string, tag: string, url: string, notes: string): Promise<string> {
  const sent = z.object({ id: z.string() }).parse(
    await fused.resend.postEmails({
      from: "Acme Releases <releases@acme.dev>",
      to: "releases@acme.dev",
      subject: `${repository} ${tag} is out`,
      text: `${notes}\n\nFull release: ${url}`,
    }),
  );
  return sent.id;
}

function releaseNotes(prs: PullRequest[], previousTag?: string): string {
  const has = (pr: PullRequest, label: string) => pr.labels.some((l) => l.name === label);
  const section = (title: string, items: PullRequest[]) =>
    items.length ? [`## ${title}`, ...items.map((pr) => `- ${pr.title} (#${pr.number})`), ""] : [];

  return [
    ...section("Features", prs.filter((pr) => has(pr, "feature"))),
    ...section("Fixes", prs.filter((pr) => has(pr, "fix"))),
    ...section("Other", prs.filter((pr) => !has(pr, "feature") && !has(pr, "fix"))),
    previousTag ? `Changes since ${previousTag}.` : "",
  ].join("\n");
}
```

Three things to notice:

- **The order is code.** The announcement can't go out before the release exists, because step 5 only runs after step 4 succeeds. The duplicate-tag check always runs first.
- **The edge cases are explicit.** A tag that's already been released, a release with nothing in it, and a result set larger than one page all fail with a clear message instead of producing something that looks almost right.
- **The contract is provider-neutral.** Callers send a repository and a tag. They get back a URL, a count and an `announcementId`, not a Resend message ID. That one decision is what makes the next section possible.

### The config

```yaml
# .fused/unified_app/publish-release.yaml
apiVersion: fused/v1
kind: unified_app
name: publish-release
version: "1.0.0"
bucket: default
source_path: publish-release.ts
services:
  github:
    version: "v3"
    operations: [reposListReleases, searchIssuesAndPullRequests, reposCreateRelease]
  resend:
    version: "1.5.0"
    operations: [postEmails]
```

This is the app's whole permission surface: four operations across two services. The GitHub token in the bucket might also be able to delete releases or push to branches, but this app can't, because those operations aren't listed.

### Add the credentials

`describe` can enable services, but it can't create your API keys. Store a GitHub token with permission to read pull requests and write releases, along with your Resend key, in the bucket the app uses:

```bash
fused-cli connect github --bucket default
fused-cli connect resend --bucket default
```

The CLI prompts for each secret without echoing it, and the credentials take effect immediately. Deploying the app registers it but doesn't run it. Save the **app family ID** and the **execution token** from the deploy, because the token is shown only once.

Your release pipeline can now publish with a single request:

```bash
curl -X POST "$FUSED_ENGINE_URL/v1/apps/$FUSED_APP_FAMILY_ID/executions" \
  -H "Authorization: Bearer $FUSED_APP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"operation":"execute","input":{"repository":"acme/web","tag":"v2.4.0"}}'
```

```json
{
  "status": "succeeded",
  "output": {
    "releaseUrl": "https://github.com/acme/web/releases/tag/v2.4.0",
    "pullRequests": 23,
    "announcementId": "4ef9a417-02e9-4d39-ad75-9611e0fcc33c"
  }
}
```

(The response is trimmed. If an execution is still running, [look up the result](https://usefused.com/docs/app/unified-apps/results-and-debugging) later.)

## Swap a provider without touching the caller

Six months later, your team decides release announcements belong in a Slack channel, not an inbox.

If the release process lived in your pipeline, that would mean a new SDK, new credentials in CI, new code and a redeploy, repeated for every place that publishes releases. With a Unified App, the change stays inside the app.

**1. Change the one function that knows about the provider.**

```typescript
// The only part of the app that knows how announcements are delivered.
async function announce(repository: string, tag: string, url: string, notes: string): Promise<string> {
  const posted = z.object({ ts: z.string() }).parse(
    await fused.slack.chatPostMessage({
      channel: "#releases",
      text: `*${repository} ${tag} is out*\n${notes}\n<${url}|Full release>`,
    }),
  );
  return posted.ts;
}
```

**2. Swap the service in the config and bump the version.**

```diff
-version: "1.0.0"
+version: "1.1.0"
 ...
 services:
   github:
     version: "v3"
     operations: [reposListReleases, searchIssuesAndPullRequests, reposCreateRelease]
-  resend:
-    version: "1.5.0"
-    operations: [postEmails]
+  slack:
+    version: "<pinned version>"
+    operations: [chatPostMessage]
```

**3. Store the Slack credential and deploy.**

```bash
fused-cli connect slack --bucket default
fused-cli app plan  -f .fused/unified_app/publish-release.yaml
fused-cli app apply -f .fused/unified_app/publish-release.yaml
```

That's the whole change. The input is still `{ repository, tag }`, and the output is still `{ releaseUrl, pullRequests, announcementId }`. The pipeline that calls the app uses the same family URL and token, so it picks up `1.1.0` without a code change or a redeploy. It never had a Resend key, and it doesn't need a Slack token.

Published versions are immutable. Redeploying changed code under an existing version number fails with `app_version_immutable`, so `1.0.0` stays exactly as it was. If the Slack version misbehaves, roll back with one command:

```bash
fused-cli app promote publish-release --version 1.0.0
```

New requests go back to the email version immediately, and your local files aren't touched.

The same pattern covers bigger changes: adding a step, changing the notes format, or moving off a provider entirely. The rule is to keep the contract and the behavior callers depend on, including what counts as success and how failures are reported. Test that, then ship a new version.

## Don't make your agent rediscover the process

Now give the same job to an agent.

The common approach is to hand it tools for GitHub and Resend and a prompt such as "Release v2.4.0 of acme/web." To do that correctly, the agent has to work out on its own that it should:

- check that `v2.4.0` hasn't already been released,
- choose the right base release, ignoring drafts,
- write a valid search query for merged pull requests and notice when results run past one page,
- create the release before announcing it,
- avoid sending a second announcement when it retries a step that failed.

A capable model will get this right most of the time. "Most of the time" isn't how you want releases to work. Each run is planned from scratch, each tool call is another round trip, and the agent holds enough access to do things you never meant it to do.

With a Unified App, the agent makes one call:

```json
{
  "name": "execute",
  "arguments": {
    "operation": "unified_app:publish_release",
    "input": { "repository": "acme/web", "tag": "v2.4.0" }
  }
}
```

The agent decides *when* to release. Your code decides *how*. The steps, the order and the edge cases are the same on every run. The agent only has access to the one action, not to every operation behind it. When something is wrong, it gets a clear error such as `Nothing merged since v2.3.0`, which it can report back instead of improvising a fix.

This is also why the provider swap matters for agents. When announcements move to Slack, the agent's prompt and tool call stay the same. It never knew about Resend.

## One app, for developers and agents

Because the process lives in Fused, not in any one caller, you can hand the same app to developers as an SDK and to agents as an MCP server. Each consumer selects the app in its own config.

**For developers**, add it to an SDK:

```yaml
apiVersion: fused/v1
kind: sdk
name: release-tools
version: "1.0.0"
language: typescript
bucket: default
unified_apps:
  publish_release:
    name: publish-release
    version: "1.1.0"
```

After `fused-cli app plan` and `apply`, the generated client exposes the app as a typed method:

```typescript
const result = await sdk.unifiedApps.publish_release({ repository: "acme/web", tag: "v2.4.0" });

if (result.status === "succeeded") {
  console.log(`Published ${result.output.pullRequests} changes: ${result.output.releaseUrl}`);
}
```

**For agents**, add it to an MCP server:

```yaml
apiVersion: fused/v1
kind: mcp
name: release-agent-tools
version: "1.0.0"
description: Release tools for the engineering assistant
bucket: default
unified_apps:
  publish_release:
    name: publish-release
    version: "1.1.0"
```

The agent calls it through the server's `execute` tool, as shown above. A Python SDK is also available (`sdk.unified_apps.publish_release(...)`), and one Unified App can call another with `fused.callApp(...)`.

Both consumers use their own execution tokens, and neither one holds a GitHub, Resend or Slack credential. SDK and MCP consumers pin an exact app version, so moving them to a new version is a one-line change to the pin in their config. Their application code and the agent's prompts stay the same. Each config can select up to 16 Unified Apps; see [calling from an SDK, MCP or another app](https://usefused.com/docs/app/unified-apps/use-from-apps) for the details.

## Good to know

- **Failures are explicit.** App calls are synchronous and aren't retried automatically. Check `status` before reading `output`, and design steps so that a retry is safe. Here, the duplicate-tag check stops a retry from publishing twice. A production version might also record whether the announcement went out, so a retry after a failed announcement can resume rather than stop.
- **Composition has limits.** Apps can call other apps up to eight levels deep, with at most 32 nested calls.
- **Users can act as themselves.** For OAuth providers, an app can act on behalf of a [connected user](https://usefused.com/docs/bucket/connect-user-accounts) instead of using a shared token.

## Get started

Unified Apps are available now.

1. [Install the CLI and sign in](https://usefused.com/docs/quickstart).
2. Run `fused-cli describe` with the process you want to automate, or start from the [Unified Apps guide](https://usefused.com/docs/app/unified-apps).
3. Call it over REST, then [give it to your developers and agents](https://usefused.com/docs/app/unified-apps/use-from-apps).

Start with the process your agents get wrong most often, or the one that would hurt most if you had to change its provider tomorrow.