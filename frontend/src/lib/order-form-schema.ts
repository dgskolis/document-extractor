import { z } from "zod";

export const orderFormSchema = z.object({
  patient_first_name: z.string().min(1, "First name is required"),
  patient_last_name: z.string().min(1, "Last name is required"),
  date_of_birth: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Enter a valid date (YYYY-MM-DD)")
    .refine((value) => {
      const date = new Date(`${value}T00:00:00`);
      const today = new Date();
      today.setHours(23, 59, 59, 999);
      return date <= today;
    }, "Date of birth cannot be in the future"),
});

export type OrderFormValues = z.infer<typeof orderFormSchema>;
