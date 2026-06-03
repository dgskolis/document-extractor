import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  formatDate,
  formatPatientName,
  formatStatusLabel,
  statusBadgeClass,
} from "@/lib/format";
import type { Order } from "@/types";

interface OrderDetailSheetProps {
  order: Order | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium">{value}</dd>
    </div>
  );
}

export function OrderDetailSheet({
  order,
  open,
  onOpenChange,
}: OrderDetailSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Order Details</SheetTitle>
          <SheetDescription>
            Full details for order {order?.id ?? ""}
          </SheetDescription>
        </SheetHeader>
        {order && (
          <dl className="flex flex-col gap-4 px-4">
            <DetailRow label="Order ID" value={order.id} />
            <DetailRow label="Patient name" value={formatPatientName(order)} />
            <DetailRow
              label="Date of birth"
              value={formatDate(order.date_of_birth)}
            />
            <DetailRow
              label="Status"
              value={
                <Badge
                  variant="secondary"
                  className={statusBadgeClass(order.status)}
                >
                  {formatStatusLabel(order.status)}
                </Badge>
              }
            />
            <DetailRow
              label="Created at"
              value={formatDate(order.created_at)}
            />
          </dl>
        )}
      </SheetContent>
    </Sheet>
  );
}
