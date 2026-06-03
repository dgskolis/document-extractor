import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useCreateOrder } from "@/hooks/useCreateOrder";
import {
  orderFormSchema,
  type OrderFormValues,
} from "@/lib/order-form-schema";
import type { ExtractedPatient } from "@/types";

interface ManualOrderFormProps {
  prefill?: ExtractedPatient | null;
  disabled?: boolean;
}

export function ManualOrderForm({
  prefill = null,
  disabled = false,
}: ManualOrderFormProps) {
  const { create, isSubmitting } = useCreateOrder();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<OrderFormValues>({
    resolver: zodResolver(orderFormSchema),
    defaultValues: {
      patient_first_name: "",
      patient_last_name: "",
      date_of_birth: "",
    },
  });

  useEffect(() => {
    if (prefill) {
      reset({
        patient_first_name: prefill.patient_first_name,
        patient_last_name: prefill.patient_last_name,
        date_of_birth: prefill.date_of_birth,
      });
    }
  }, [prefill, reset]);

  const onSubmit = handleSubmit(async (values) => {
    try {
      await create(values);
      toast.success("Order created successfully");
      reset({
        patient_first_name: "",
        patient_last_name: "",
        date_of_birth: "",
      });
    } catch {
      // Error toast handled globally by mutation cache
    }
  });

  const isDisabled = disabled || isSubmitting;

  return (
    <form onSubmit={onSubmit}>
      <FieldSet disabled={isDisabled}>
        <FieldLegend>Create Order Manually</FieldLegend>
        <FieldGroup>
          <Field data-invalid={!!errors.patient_first_name || undefined}>
            <FieldLabel htmlFor="patient_first_name">First name</FieldLabel>
            <Input
              id="patient_first_name"
              autoComplete="given-name"
              disabled={isDisabled}
              aria-invalid={!!errors.patient_first_name}
              {...register("patient_first_name")}
            />
            <FieldError errors={[errors.patient_first_name]} />
          </Field>
          <Field data-invalid={!!errors.patient_last_name || undefined}>
            <FieldLabel htmlFor="patient_last_name">Last name</FieldLabel>
            <Input
              id="patient_last_name"
              autoComplete="family-name"
              disabled={isDisabled}
              aria-invalid={!!errors.patient_last_name}
              {...register("patient_last_name")}
            />
            <FieldError errors={[errors.patient_last_name]} />
          </Field>
          <Field data-invalid={!!errors.date_of_birth || undefined}>
            <FieldLabel htmlFor="date_of_birth">Date of birth</FieldLabel>
            <Input
              id="date_of_birth"
              type="date"
              disabled={isDisabled}
              aria-invalid={!!errors.date_of_birth}
              {...register("date_of_birth")}
            />
            <FieldError errors={[errors.date_of_birth]} />
          </Field>
          <Field orientation="horizontal">
            <Button type="submit" disabled={isDisabled}>
              {isSubmitting ? "Creating..." : "Create Order"}
            </Button>
          </Field>
        </FieldGroup>
      </FieldSet>
    </form>
  );
}
