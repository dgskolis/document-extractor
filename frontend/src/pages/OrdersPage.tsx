import { useState } from "react";
import { Link } from "react-router-dom";

import { BackendErrorBanner } from "@/components/errors/backend-error-banner";
import { columns } from "@/components/orders/columns";
import { OrderDetailSheet } from "@/components/orders/order-detail-sheet";
import { OrdersEmptyState } from "@/components/orders/orders-empty-state";
import { OrdersTableSkeleton } from "@/components/orders/orders-table-skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/ui/data-table";
import { useOrders } from "@/hooks/useOrders";
import { usePageTitle } from "@/hooks/usePageTitle";
import type { Order } from "@/types";

export default function OrdersPage() {
  usePageTitle("Orders");

  const { orders, loading, error, isUnreachable, refetch } = useOrders();
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  const handleRowClick = (order: Order) => {
    setSelectedOrder(order);
    setSheetOpen(true);
  };

  const handleSheetOpenChange = (open: boolean) => {
    setSheetOpen(open);
    if (!open) {
      setSelectedOrder(null);
    }
  };

  const showTable = !loading && !isUnreachable && !error && orders.length > 0;
  const showEmpty = !loading && !isUnreachable && !error && orders.length === 0;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">Orders</h1>
          {showTable && (
            <Badge variant="secondary">{orders.length}</Badge>
          )}
        </div>
        {!isUnreachable && (
          <Button render={<Link to="/upload" />}>Upload Document</Button>
        )}
      </div>

      {loading && <OrdersTableSkeleton />}

      {isUnreachable && (
        <BackendErrorBanner onRetry={() => void refetch()} />
      )}

      {error && !isUnreachable && (
        <p className="py-8 text-center text-destructive">{error}</p>
      )}

      {showEmpty && <OrdersEmptyState />}

      {showTable && (
        <div className="overflow-x-auto">
          <DataTable
            columns={columns}
            data={orders}
            initialSorting={[{ id: "created_at", desc: true }]}
            onRowClick={handleRowClick}
          />
        </div>
      )}

      <OrderDetailSheet
        order={selectedOrder}
        open={sheetOpen}
        onOpenChange={handleSheetOpenChange}
      />
    </div>
  );
}
