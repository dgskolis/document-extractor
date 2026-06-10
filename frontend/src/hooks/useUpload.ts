import { useMutation } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import { uploadDocument } from "@/api/orders";
import { isUploadDocumentError } from "@/api/upload-errors";
import {
  getMissingExtractionFields,
  hasExtractedPatientData,
  isExtractedPatientComplete,
  isExtractedPatientEmpty,
} from "@/lib/extraction";
import type { ExtractedPatient } from "@/types";

export type ExtractionStatus = "idle" | "complete" | "partial" | "failed";

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
  const [extractionStatus, setExtractionStatus] =
    useState<ExtractionStatus>("idle");
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [referenceId, setReferenceId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: (result) => {
      setProgress(100);
      setReferenceId(null);

      if (isExtractedPatientEmpty(result)) {
        setExtractedPatient(null);
        setMissingFields([]);
        setExtractionStatus("failed");
        return;
      }

      setExtractedPatient(result);
      if (isExtractedPatientComplete(result)) {
        setMissingFields([]);
        setExtractionStatus("complete");
        return;
      }

      setMissingFields(getMissingExtractionFields(result));
      setExtractionStatus("partial");
    },
    onError: (error) => {
      if (isUploadDocumentError(error)) {
        setReferenceId(error.referenceId);
        if (error.partialPatient && hasExtractedPatientData(error.partialPatient)) {
          setExtractedPatient(error.partialPatient);
          setMissingFields(getMissingExtractionFields(error.partialPatient));
          setExtractionStatus("partial");
        } else {
          setExtractedPatient(null);
          setMissingFields([]);
          setExtractionStatus("failed");
        }
        setProgress(0);
        return;
      }

      setExtractedPatient(null);
      setReferenceId(null);
      setMissingFields([]);
      setExtractionStatus("failed");
      setProgress(0);
    },
  });

  const selectFile = useCallback((selectedFile: File | null): boolean => {
    if (!selectedFile) {
      setFile(null);
      setExtractedPatient(null);
      setExtractionStatus("idle");
      setMissingFields([]);
      setReferenceId(null);
      setProgress(0);
      return true;
    }

    if (!isPdfFile(selectedFile)) {
      return false;
    }

    setFile(selectedFile);
    setExtractedPatient(null);
    setExtractionStatus("idle");
    setMissingFields([]);
    setReferenceId(null);
    setProgress(0);
    return true;
  }, []);

  const clearFile = useCallback(() => {
    setFile(null);
    setExtractedPatient(null);
    setExtractionStatus("idle");
    setMissingFields([]);
    setReferenceId(null);
    setProgress(0);
  }, []);

  const processDocument = useCallback(async () => {
    if (!file || uploadMutation.isPending) {
      return;
    }

    setProgress(0);
    setExtractedPatient(null);
    setExtractionStatus("idle");
    setMissingFields([]);
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
    extractionStatus,
    missingFields,
    referenceId,
    processing: uploadMutation.isPending,
    progress,
    selectFile,
    clearFile,
    processDocument,
  };
}
