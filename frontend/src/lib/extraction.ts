import type { ExtractedPatient } from "@/types";

type ExtractionFieldKey = keyof ExtractedPatient;

const EXTRACTION_FIELD_LABELS: Record<ExtractionFieldKey, string> = {
  patient_first_name: "First name",
  patient_last_name: "Last name",
  date_of_birth: "Date of birth",
};

function isExtractedPatientEmpty(patient: ExtractedPatient): boolean {
  return (
    !patient.patient_first_name &&
    !patient.patient_last_name &&
    !patient.date_of_birth
  );
}

function isExtractedPatientComplete(patient: ExtractedPatient): boolean {
  return (
    Boolean(patient.patient_first_name) &&
    Boolean(patient.patient_last_name) &&
    Boolean(patient.date_of_birth)
  );
}

function hasExtractedPatientData(patient: ExtractedPatient): boolean {
  return !isExtractedPatientEmpty(patient);
}

function isPartialExtraction(patient: ExtractedPatient): boolean {
  return hasExtractedPatientData(patient) && !isExtractedPatientComplete(patient);
}

function getMissingExtractionFields(patient: ExtractedPatient): string[] {
  return (Object.keys(EXTRACTION_FIELD_LABELS) as ExtractionFieldKey[])
    .filter((field) => !patient[field])
    .map((field) => EXTRACTION_FIELD_LABELS[field]);
}

export {
  getMissingExtractionFields,
  hasExtractedPatientData,
  isExtractedPatientComplete,
  isExtractedPatientEmpty,
  isPartialExtraction,
};
