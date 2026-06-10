import { useState } from "react";
import { toast } from "sonner";

import { ExtractedDataCard } from "@/components/upload/extracted-data-card";
import { DocumentUploadSection } from "@/components/upload/document-upload-section";
import { ManualOrderForm } from "@/components/upload/manual-order-form";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { GENERIC_UPLOAD_ERROR_MESSAGE } from "@/api/upload-errors";
import { usePageTitle } from "@/hooks/usePageTitle";
import { useUpload } from "@/hooks/useUpload";
import type { ExtractedPatient } from "@/types";

function formatMissingFieldsMessage(fields: string[]): string {
  if (fields.length === 1) {
    return `We couldn't extract ${fields[0]}. Please complete the missing value below.`;
  }

  return `We couldn't extract the following fields: ${fields.join(", ")}. Please complete the missing values below.`;
}

export default function UploadPage() {
  usePageTitle("Upload");

  const {
    file,
    extractedPatient,
    extractionStatus,
    missingFields,
    referenceId,
    processing,
    progress,
    selectFile,
    processDocument,
  } = useUpload();
  const [manualPrefill, setManualPrefill] = useState<ExtractedPatient | null>(
    null,
  );

  const formPrefill =
    extractionStatus === "partial" ? extractedPatient : manualPrefill;

  const handleFileSelect = (selectedFile: File) => {
    const accepted = selectFile(selectedFile);
    if (!accepted) {
      toast.error("Only PDF files are accepted");
    }
  };

  const handlePrefill = (data: ExtractedPatient) => {
    setManualPrefill(data);
    toast.success("Form pre-filled with extracted data");
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold tracking-tight">Upload</h1>

      <ManualOrderForm prefill={formPrefill} disabled={processing} />

      <Separator />

      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-medium">Upload Document</h2>
        <DocumentUploadSection
          file={file}
          processing={processing}
          progress={progress}
          disabled={processing}
          onFileSelect={handleFileSelect}
          onProcess={() => void processDocument()}
        />
        {extractionStatus === "failed" && !processing && (
          <Alert variant="destructive">
            <AlertTitle>Extraction failed</AlertTitle>
            <AlertDescription>
              {GENERIC_UPLOAD_ERROR_MESSAGE}
              {referenceId ? (
                <>
                  {" "}
                  Reference: <span className="font-mono">{referenceId}</span>
                </>
              ) : null}
            </AlertDescription>
          </Alert>
        )}
        {extractionStatus === "partial" && !processing && missingFields.length > 0 && (
          <Alert>
            <AlertTitle>Partial extraction</AlertTitle>
            <AlertDescription>
              {formatMissingFieldsMessage(missingFields)}
            </AlertDescription>
          </Alert>
        )}
        {extractedPatient &&
          (extractionStatus === "complete" || extractionStatus === "partial") &&
          !processing && (
          <ExtractedDataCard
            data={extractedPatient}
            onPrefill={handlePrefill}
          />
        )}
      </div>
    </div>
  );
}
