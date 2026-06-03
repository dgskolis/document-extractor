import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatDate } from "@/lib/format";
import type { ExtractedPatient } from "@/types";

interface ExtractedDataCardProps {
  data: ExtractedPatient;
  onPrefill: (data: ExtractedPatient) => void;
}

function DataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
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
        <DataRow label="First name" value={data.patient_first_name} />
        <DataRow label="Last name" value={data.patient_last_name} />
        <DataRow label="Date of birth" value={formatDate(data.date_of_birth)} />
      </CardContent>
      <CardFooter>
        <Button type="button" onClick={() => onPrefill(data)}>
          Fill Order with this Data
        </Button>
      </CardFooter>
    </Card>
  );
}
