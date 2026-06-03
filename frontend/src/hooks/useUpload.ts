import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import { uploadDocument } from "@/api/orders";
import { ORDERS_QUERY_KEY } from "@/hooks/useOrders";
import type { ExtractedPatient } from "@/types";

const PDF_MIME = "application/pdf";

function isPdfFile(file: File): boolean {
  return (
    file.type === PDF_MIME || file.name.toLowerCase().endsWith(".pdf")
  );
}

export function useUpload() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [extractedPatient, setExtractedPatient] =
    useState<ExtractedPatient | null>(null);
  const [progress, setProgress] = useState(0);

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: async (result) => {
      setProgress(100);
      setExtractedPatient(result);
      await queryClient.invalidateQueries({ queryKey: ORDERS_QUERY_KEY });
    },
  });

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
    if (!file || uploadMutation.isPending) {
      return;
    }

    setProgress(0);
    setExtractedPatient(null);

    const startTime = Date.now();
    const progressInterval = window.setInterval(() => {
      const elapsed = Date.now() - startTime;
      const nextProgress = Math.min(95, Math.round(elapsed / 20));
      setProgress(nextProgress);
    }, 50);

    try {
      await uploadMutation.mutateAsync(file);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to process document";
      toast.error(message);
      setProgress(0);
    } finally {
      window.clearInterval(progressInterval);
    }
  }, [file, uploadMutation]);

  return {
    file,
    extractedPatient,
    processing: uploadMutation.isPending,
    progress,
    selectFile,
    clearFile,
    processDocument,
  };
}
