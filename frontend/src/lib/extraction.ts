import type { ExtractedPatient } from "@/types";

function isExtractedPatientEmpty(patient: ExtractedPatient): boolean {
  return (
    !patient.patient_first_name ||
    !patient.patient_last_name ||
    !patient.date_of_birth
  );
}

function hasExtractedPatientData(patient: ExtractedPatient): boolean {
  return Boolean(
    patient.patient_first_name ||
      patient.patient_last_name ||
      patient.date_of_birth,
  );
}

export { hasExtractedPatientData, isExtractedPatientEmpty };
