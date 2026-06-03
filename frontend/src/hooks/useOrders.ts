import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { isNetworkError } from "@/api/client";
import {
  createOrder,
  deleteOrder,
  getOrders,
  updateOrder,
} from "@/api/orders";
import type { OrderCreateInput, OrderUpdateInput } from "@/types";

export const ORDERS_QUERY_KEY = ["orders"] as const;

export function useOrders() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ORDERS_QUERY_KEY,
    queryFn: getOrders,
  });

  const createMutation = useMutation({
    mutationFn: (input: OrderCreateInput) => createOrder(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ORDERS_QUERY_KEY });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: OrderUpdateInput }) =>
      updateOrder(id, input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ORDERS_QUERY_KEY });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteOrder(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ORDERS_QUERY_KEY });
    },
  });

  return {
    orders: query.data ?? [],
    loading: query.isLoading,
    error: query.error?.message ?? null,
    isUnreachable: query.isError && isNetworkError(query.error),
    refetch: query.refetch,
    createOrder: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    updateOrder: (id: string, input: OrderUpdateInput) =>
      updateMutation.mutateAsync({ id, input }),
    deleteOrder: deleteMutation.mutateAsync,
  };
}
