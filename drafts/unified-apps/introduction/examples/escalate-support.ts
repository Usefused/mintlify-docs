import { z } from "zod";
import { buildUnifiedApp } from "@fused/unified-app";
import { services } from "@fused/operations";

// Fix the owning team's repository so callers cannot redirect escalations.
const REPO_OWNER = "your-org";
const REPO_NAME = "support-escalations";

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
    const rawIssue = await services.github.createIssue({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      "X-GitHub-Api-Version": "2026-03-10",
      Accept: "application/vnd.github+json",
      title: `${input.caseId}: ${input.title}`,
      body: `Requester: ${input.requesterEmail}\n\n${input.details}`,
    });
    // Validate the provider result before exposing identifiers or notifying anyone.
    const issue = z.object({ id: z.number().int(), html_url: z.string().url() }).parse(rawIssue);
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
        text: `An engineering issue needs attention:\n${issue.html_url}`,
      });
      // HTTP success alone is insufficient if the provider omits its message ID.
      z.object({ id: z.string().min(1) }).parse(sent);
      // Mark acceptance only after validating the provider acknowledgement.
      notification = "accepted";
    } catch {
      // Keep needs_attention; recreating the issue would make recovery worse.
    }
    return { issueId, issueUrl: issue.html_url, notification };
  },
});
