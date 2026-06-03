import { Button } from "@/components/ui/button";
import { DocumentDropzone } from "@/components/upload/document-dropzone";
import { Progress, ProgressLabel, ProgressValue } from "@/components/ui/progress";

interface DocumentUploadSectionProps {
  file: File | null;
  processing: boolean;
  progress: number;
  onFileSelect: (file: File) => void;
  onProcess: () => void;
}

export function DocumentUploadSection({
  file,
  processing,
  progress,
  onFileSelect,
  onProcess,
}: DocumentUploadSectionProps) {
  return (
    <div className="flex flex-col gap-4">
      <DocumentDropzone
        disabled={processing}
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
          {!processing && progress < 100 && (
            <Button type="button" onClick={onProcess}>
              Process Document
            </Button>
          )}
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
