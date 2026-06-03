import { useOrders } from "@/hooks/useOrders";

export function useCreateOrder() {
  const { createOrder, isCreating } = useOrders();

  return {
    create: createOrder,
    isSubmitting: isCreating,
  };
}
