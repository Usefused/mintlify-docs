import { z } from "zod";
import { buildUnifiedApp } from "@fused/unified-app";
import { fused } from "@fused/operations";

const rateSchema = z.object({
  base: z.string(),
  quote: z.string(),
  date: z.string().date(),
  rate: z.number().positive(),
});

export default buildUnifiedApp({
  input: z.object({
    amount: z.number().nonnegative(),
    base: z.string().length(3),
    quote: z.string().length(3),
    date: z.string().date(),
  }),
  output: z.object({
    amount: z.number(),
    base: z.string(),
    quote: z.string(),
    rate: z.number(),
    rateDate: z.string(),
    convertedAmount: z.number(),
  }),
  // Validate the provider result before producing a display-oriented quote.
  async execute({ input }) {
    const response = await fused.frankfurter.getRate({
      base: input.base,
      quote: input.quote,
      date: input.date,
    });
    const rate = rateSchema.parse(response);
    return {
      amount: input.amount,
      base: rate.base,
      quote: rate.quote,
      rate: rate.rate,
      rateDate: rate.date,
      convertedAmount: Math.round(input.amount * rate.rate * 100) / 100,
    };
  },
});
