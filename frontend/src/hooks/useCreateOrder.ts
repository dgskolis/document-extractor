import { useState } from "react";

import { createOrder } from "@/api/orders";
import type { OrderCreateInput } from "@/types";

export function useCreateOrder() {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const create = async (input: OrderCreateInput) => {
    setIsSubmitting(true);
    try {
      return await createOrder(input);
    } finally {
      setIsSubmitting(false);
    }
  };

  return { create, isSubmitting };
}
