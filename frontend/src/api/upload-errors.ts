import type { ExtractedPatient } from "@/types";

export const GENERIC_UPLOAD_ERROR_MESSAGE =
  "We couldn't extract information from this document. Please fill in the form manually.";

export class UploadDocumentError extends Error {
  readonly referenceId: string | null;
  readonly partialPatient: ExtractedPatient | null;

  constructor(
    partialPatient: ExtractedPatient | null,
    referenceId: string | null = null,
  ) {
    super(GENERIC_UPLOAD_ERROR_MESSAGE);
    this.name = "UploadDocumentError";
    this.partialPatient = partialPatient;
    this.referenceId = referenceId;
  }
}

export function isUploadDocumentError(
  error: unknown,
): error is UploadDocumentError {
  return error instanceof UploadDocumentError;
}
