import { useCallback, useState } from "react";

import { uploadDocument } from "@/api/orders";
import type { ExtractedPatient } from "@/types";

const PDF_MIME = "application/pdf";
const PROGRESS_DURATION_MS = 2000;

function isPdfFile(file: File): boolean {
  return (
    file.type === PDF_MIME || file.name.toLowerCase().endsWith(".pdf")
  );
}

export function useUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [extractedPatient, setExtractedPatient] =
    useState<ExtractedPatient | null>(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);

  const selectFile = useCallback((selectedFile: File | null): boolean => {
    if (!selectedFile) {
      setFile(null);
      setExtractedPatient(null);
      setProgress(0);
      return true;
    }

    if (!isPdfFile(selectedFile)) {
      return false;
    }

    setFile(selectedFile);
    setExtractedPatient(null);
    setProgress(0);
    return true;
  }, []);

  const clearFile = useCallback(() => {
    setFile(null);
    setExtractedPatient(null);
    setProgress(0);
  }, []);

  const processDocument = useCallback(async () => {
    if (!file || processing) {
      return;
    }

    setProcessing(true);
    setProgress(0);
    setExtractedPatient(null);

    const startTime = Date.now();
    const progressInterval = window.setInterval(() => {
      const elapsed = Date.now() - startTime;
      const nextProgress = Math.min(
        100,
        Math.round((elapsed / PROGRESS_DURATION_MS) * 100),
      );
      setProgress(nextProgress);
    }, 50);

    try {
      const result = await uploadDocument(file);
      setProgress(100);
      setExtractedPatient(result);
    } finally {
      window.clearInterval(progressInterval);
      setProcessing(false);
    }
  }, [file, processing]);

  return {
    file,
    extractedPatient,
    processing,
    progress,
    selectFile,
    clearFile,
    processDocument,
  };
}
