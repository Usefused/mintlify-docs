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
