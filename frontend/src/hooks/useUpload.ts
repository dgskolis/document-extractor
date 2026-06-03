import { useMutation } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import { uploadDocument } from "@/api/orders";
import { isUploadDocumentError } from "@/api/upload-errors";
import {
  hasExtractedPatientData,
  isExtractedPatientEmpty,
} from "@/lib/extraction";
import type { ExtractedPatient } from "@/types";

const PDF_MIME = "application/pdf";

function isPdfFile(file: File): boolean {
  return (
    file.type === PDF_MIME || file.name.toLowerCase().endsWith(".pdf")
  );
}

export function useUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [extractedPatient, setExtractedPatient] =
    useState<ExtractedPatient | null>(null);
  const [extractionFailed, setExtractionFailed] = useState(false);
  const [referenceId, setReferenceId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: (result) => {
      setProgress(100);
      setReferenceId(null);

      if (isExtractedPatientEmpty(result)) {
        setExtractedPatient(null);
        setExtractionFailed(true);
        return;
      }

      setExtractedPatient(result);
      setExtractionFailed(false);
    },
    onError: (error) => {
      if (isUploadDocumentError(error)) {
        setReferenceId(error.referenceId);
        if (error.partialPatient && hasExtractedPatientData(error.partialPatient)) {
          setExtractedPatient(error.partialPatient);
        } else {
          setExtractedPatient(null);
        }
        setExtractionFailed(true);
        setProgress(0);
        return;
      }

      setExtractedPatient(null);
      setReferenceId(null);
      setExtractionFailed(true);
      setProgress(0);
    },
  });

  const selectFile = useCallback((selectedFile: File | null): boolean => {
    if (!selectedFile) {
      setFile(null);
      setExtractedPatient(null);
      setExtractionFailed(false);
      setReferenceId(null);
      setProgress(0);
      return true;
    }

    if (!isPdfFile(selectedFile)) {
      return false;
    }

    setFile(selectedFile);
    setExtractedPatient(null);
    setExtractionFailed(false);
    setReferenceId(null);
    setProgress(0);
    return true;
  }, []);

  const clearFile = useCallback(() => {
    setFile(null);
    setExtractedPatient(null);
    setExtractionFailed(false);
    setReferenceId(null);
    setProgress(0);
  }, []);

  const processDocument = useCallback(async () => {
    if (!file || uploadMutation.isPending) {
      return;
    }

    setProgress(0);
    setExtractedPatient(null);
    setExtractionFailed(false);
    setReferenceId(null);

    const startTime = Date.now();
    const progressInterval = window.setInterval(() => {
      const elapsed = Date.now() - startTime;
      const nextProgress = Math.min(95, Math.round(elapsed / 20));
      setProgress(nextProgress);
    }, 50);

    try {
      await uploadMutation.mutateAsync(file);
    } catch {
      setProgress(0);
    } finally {
      window.clearInterval(progressInterval);
    }
  }, [file, uploadMutation]);

  return {
    file,
    extractedPatient,
    extractionFailed,
    referenceId,
    processing: uploadMutation.isPending,
    progress,
    selectFile,
    clearFile,
    processDocument,
  };
}
