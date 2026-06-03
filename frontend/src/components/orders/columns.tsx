import type { ColumnDef } from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  formatDate,
  formatPatientName,
  formatStatusLabel,
  statusBadgeClass,
} from "@/lib/format";
import type { Order } from "@/types";

export const columns: ColumnDef<Order>[] = [
  {
    id: "patient_name",
    header: "Patient name",
    cell: ({ row }) => formatPatientName(row.original),
  },
  {
    accessorKey: "date_of_birth",
    header: "Date of birth",
    cell: ({ row }) => formatDate(row.original.date_of_birth),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => (
      <Badge
        variant="secondary"
        className={statusBadgeClass(row.original.status)}
      >
        {formatStatusLabel(row.original.status)}
      </Badge>
    ),
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (
      <Button
        variant="ghost"
        className="-ml-2 h-8"
        onClick={() =>
          column.toggleSorting(column.getIsSorted() === "asc")
        }
      >
        Created at
        {column.getIsSorted() === "asc" ? (
          <ArrowUp className="ml-2 size-4" />
        ) : column.getIsSorted() === "desc" ? (
          <ArrowDown className="ml-2 size-4" />
        ) : (
          <ArrowUpDown className="ml-2 size-4" />
        )}
      </Button>
    ),
    cell: ({ row }) => formatDate(row.original.created_at),
  },
];
