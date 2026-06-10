import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatDateOptional } from "@/lib/format";
import type { ExtractedPatient } from "@/types";

interface ExtractedDataCardProps {
  data: ExtractedPatient;
  onPrefill: (data: ExtractedPatient) => void;
}

function DataRow({ label, value }: { label: string; value: string }) {
  const isMissing = value === "Not extracted";

  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span
        className={
          isMissing ? "text-sm text-muted-foreground italic" : "text-sm font-medium"
        }
      >
        {value}
      </span>
    </div>
  );
}

export function ExtractedDataCard({ data, onPrefill }: ExtractedDataCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Extracted Data</CardTitle>
        <CardDescription>
          Patient information extracted from the uploaded document.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <DataRow
          label="First name"
          value={data.patient_first_name || "Not extracted"}
        />
        <DataRow
          label="Last name"
          value={data.patient_last_name || "Not extracted"}
        />
        <DataRow
          label="Date of birth"
          value={formatDateOptional(data.date_of_birth)}
        />
      </CardContent>
      <CardFooter>
        <Button type="button" onClick={() => onPrefill(data)}>
          Fill Order with this Data
        </Button>
      </CardFooter>
    </Card>
  );
}
