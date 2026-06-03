import { useState } from "react";
import { Link } from "react-router-dom";

import { columns } from "@/components/orders/columns";
import { OrderDetailSheet } from "@/components/orders/order-detail-sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/ui/data-table";
import { useOrders } from "@/hooks/useOrders";
import type { Order } from "@/types";

export default function OrdersPage() {
  const { orders, loading, error } = useOrders();
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

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">Orders</h1>
          {!loading && !error && (
            <Badge variant="secondary">{orders.length}</Badge>
          )}
        </div>
        <Button render={<Link to="/upload" />}>Upload Document</Button>
      </div>

      {loading && (
        <p className="py-8 text-center text-muted-foreground">
          Loading orders...
        </p>
      )}

      {error && (
        <p className="py-8 text-center text-destructive">{error}</p>
      )}

      {!loading && !error && (
        <DataTable
          columns={columns}
          data={orders}
          initialSorting={[{ id: "created_at", desc: true }]}
          onRowClick={handleRowClick}
        />
      )}

      <OrderDetailSheet
        order={selectedOrder}
        open={sheetOpen}
        onOpenChange={handleSheetOpenChange}
      />
    </div>
  );
}
