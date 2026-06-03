import { Loader2Icon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DocumentDropzone } from "@/components/upload/document-dropzone";
import { Progress, ProgressLabel, ProgressValue } from "@/components/ui/progress";

interface DocumentUploadSectionProps {
  file: File | null;
  processing: boolean;
  progress: number;
  disabled?: boolean;
  onFileSelect: (file: File) => void;
  onProcess: () => void;
}

export function DocumentUploadSection({
  file,
  processing,
  progress,
  disabled = false,
  onFileSelect,
  onProcess,
}: DocumentUploadSectionProps) {
  const isDisabled = disabled || processing;

  return (
    <div className="flex flex-col gap-4">
      <DocumentDropzone
        disabled={isDisabled}
        onFileSelect={(selectedFile) => {
          onFileSelect(selectedFile);
        }}
      />

      {file && (
        <div className="flex flex-col gap-3 rounded-lg border bg-background p-4">
          <p className="text-sm">
            <span className="text-muted-foreground">Selected file: </span>
            <span className="font-medium">{file.name}</span>
          </p>
          <Button type="button" disabled={isDisabled} onClick={onProcess}>
            {processing && (
              <Loader2Icon className="animate-spin" data-icon="inline-start" />
            )}
            Process Document
          </Button>
        </div>
      )}

      {processing && (
        <Progress value={progress}>
          <ProgressLabel>Processing document</ProgressLabel>
          <ProgressValue />
        </Progress>
      )}
    </div>
  );
}
