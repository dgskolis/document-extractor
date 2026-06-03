import { useState } from "react";
import { toast } from "sonner";

import { ExtractedDataCard } from "@/components/upload/extracted-data-card";
import { DocumentUploadSection } from "@/components/upload/document-upload-section";
import { ManualOrderForm } from "@/components/upload/manual-order-form";
import { Separator } from "@/components/ui/separator";
import { useUpload } from "@/hooks/useUpload";
import type { ExtractedPatient } from "@/types";

export default function UploadPage() {
  const {
    file,
    extractedPatient,
    processing,
    progress,
    selectFile,
    processDocument,
  } = useUpload();
  const [prefillData, setPrefillData] = useState<ExtractedPatient | null>(
    null,
  );

  const handleFileSelect = (selectedFile: File) => {
    const accepted = selectFile(selectedFile);
    if (!accepted) {
      toast.error("Only PDF files are accepted");
    }
  };

  const handlePrefill = (data: ExtractedPatient) => {
    setPrefillData(data);
    toast.success("Form pre-filled with extracted data");
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold tracking-tight">Upload</h1>

      <ManualOrderForm prefill={prefillData} />

      <Separator />

      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-medium">Upload Document</h2>
        <DocumentUploadSection
          file={file}
          processing={processing}
          progress={progress}
          onFileSelect={handleFileSelect}
          onProcess={() => void processDocument()}
        />
        {extractedPatient && !processing && (
          <ExtractedDataCard
            data={extractedPatient}
            onPrefill={handlePrefill}
          />
        )}
      </div>
    </div>
  );
}
