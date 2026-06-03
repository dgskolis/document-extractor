import { useState } from "react";

import type { ExtractedPatient } from "../types";

export function useUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [extractedPatient, setExtractedPatient] =
    useState<ExtractedPatient | null>(null);
  const [uploading, setUploading] = useState(false);

  const selectFile = (selectedFile: File | null) => {
    setFile(selectedFile);
    setExtractedPatient(null);
  };

  const upload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      // TODO: replace with real upload API call
      await Promise.resolve();
    } finally {
      setUploading(false);
    }
  };

  return {
    file,
    extractedPatient,
    uploading,
    selectFile,
    upload,
    setExtractedPatient,
  };
}
