import { useRef, useState } from "react";
import { UploadIcon } from "lucide-react";

import { cn } from "@/lib/utils";

interface DocumentDropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export function DocumentDropzone({
  onFileSelect,
  disabled = false,
}: DocumentDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFiles = (files: FileList | null) => {
    if (!files?.length || disabled) {
      return;
    }
    onFileSelect(files[0]);
  };

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      className={cn(
        "flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed px-6 py-10 text-center transition-colors",
        isDragOver
          ? "border-primary bg-muted/50"
          : "border-border bg-background",
        disabled
          ? "cursor-not-allowed opacity-50"
          : "cursor-pointer hover:bg-muted/30",
      )}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(event) => {
        if (disabled) {
          return;
        }
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) {
          setIsDragOver(true);
        }
      }}
      onDragLeave={(event) => {
        event.preventDefault();
        setIsDragOver(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setIsDragOver(false);
        handleFiles(event.dataTransfer.files);
      }}
    >
      <UploadIcon className="size-8 text-muted-foreground" />
      <p className="text-sm font-medium">Drag and drop a PDF here</p>
      <p className="text-sm text-muted-foreground">or click to browse</p>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="sr-only"
        disabled={disabled}
        onChange={(event) => handleFiles(event.target.files)}
      />
    </div>
  );
}
