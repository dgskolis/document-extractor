import logging

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_order_or_404, verify_api_key
from app.exceptions import (
    FileTooLargeError,
    OpenAIConfigurationError,
    PatientExtractionError,
    TextExtractionError,
    UnsupportedMediaTypeError,
)
from app.logging_context import generate_reference_id, log_upload_event
from app.models.order import Order
from app.schemas.document import (
    DocumentUploadResponse,
    build_order_create_from_extraction,
    build_partial_extraction_detail,
    build_text_extraction_error_detail,
    build_upload_error_detail,
)
from app.schemas.order import OrderCreate, OrderListResponse, OrderResponse, OrderUpdate
from app.schemas.upload_errors import (
    REASON_FILE_TOO_LARGE,
    REASON_LLM_EXTRACTION_FAILED,
    REASON_OPENAI_NOT_CONFIGURED,
    REASON_PARTIAL_EXTRACTION,
    REASON_TEXT_EXTRACTION_FAILED,
    REASON_UNSUPPORTED_MEDIA_TYPE,
)
from app.services import document_service, order_service, patient_extraction_service

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["orders"],
    dependencies=[Depends(verify_api_key)],
)

DEFAULT_LIST_LIMIT = 100
MAX_LIST_LIMIT = 1000


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)) -> OrderResponse:
    return order_service.create_order(db, order_in)


@router.get("/", response_model=OrderListResponse)
def list_orders(
    db: Session = Depends(get_db),
    limit: int = Query(default=DEFAULT_LIST_LIMIT, ge=1, le=MAX_LIST_LIMIT, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
) -> OrderListResponse:
    orders, total = order_service.list_orders(db, limit=limit, offset=offset)
    return OrderListResponse(items=orders, total=total, limit=limit, offset=offset)


@router.post(
    "/upload-document",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    reference_id = generate_reference_id()
    content_type = file.content_type

    try:
        content = document_service.read_upload_content(file)
    except FileTooLargeError as exc:
        log_upload_event(
            logging.WARNING,
            "Upload rejected because file exceeds size limit",
            reference_id=reference_id,
            stage="upload_read",
            reason_code=REASON_FILE_TOO_LARGE,
            content_type=content_type,
        )
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=build_upload_error_detail(reference_id=reference_id),
        ) from exc

    try:
        document_text = document_service.extract_text(
            content,
            content_type=content_type,
            filename=file.filename,
            reference_id=reference_id,
        )
    except UnsupportedMediaTypeError as exc:
        log_upload_event(
            logging.WARNING,
            "Upload rejected due to unsupported media type",
            reference_id=reference_id,
            stage="text_extraction",
            reason_code=REASON_UNSUPPORTED_MEDIA_TYPE,
            content_type=content_type,
            content_length=len(content),
        )
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=build_upload_error_detail(reference_id=reference_id),
        ) from exc
    except TextExtractionError as exc:
        log_upload_event(
            logging.WARNING,
            "Upload failed during text extraction",
            reference_id=reference_id,
            stage="text_extraction",
            reason_code=REASON_TEXT_EXTRACTION_FAILED,
            content_type=content_type,
            content_length=len(content),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=build_text_extraction_error_detail(reference_id=reference_id),
        ) from exc

    try:
        extracted_fields = patient_extraction_service.extract_patient_fields(
            document_text,
            reference_id=reference_id,
        )
    except OpenAIConfigurationError as exc:
        log_upload_event(
            logging.ERROR,
            "Upload failed because OpenAI is not configured",
            reference_id=reference_id,
            stage="patient_extraction",
            reason_code=REASON_OPENAI_NOT_CONFIGURED,
            text_length=len(document_text),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=build_upload_error_detail(reference_id=reference_id),
        ) from exc
    except PatientExtractionError as exc:
        log_upload_event(
            logging.ERROR,
            "Upload failed during patient field extraction",
            reference_id=reference_id,
            stage="patient_extraction",
            reason_code=REASON_LLM_EXTRACTION_FAILED,
            text_length=len(document_text),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=build_upload_error_detail(reference_id=reference_id),
        ) from exc

    order_in = build_order_create_from_extraction(extracted_fields, reference_id=reference_id)
    if order_in is None:
        log_upload_event(
            logging.WARNING,
            "Upload completed with partial patient field extraction",
            reference_id=reference_id,
            stage="order_validation",
            reason_code=REASON_PARTIAL_EXTRACTION,
            text_length=len(document_text),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=build_partial_extraction_detail(extracted_fields, reference_id=reference_id),
        )

    log_upload_event(
        logging.INFO,
        "Upload completed successfully",
        reference_id=reference_id,
        stage="complete",
        reason_code="upload_completed",
        content_type=content_type,
        content_length=len(content),
        text_length=len(document_text),
    )
    return DocumentUploadResponse(extraction=extracted_fields)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order: Order = Depends(get_order_or_404)) -> OrderResponse:
    return order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_in: OrderUpdate,
    order: Order = Depends(get_order_or_404),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return order_service.update_order(db, order, order_in)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order: Order = Depends(get_order_or_404),
    db: Session = Depends(get_db),
) -> None:
    order_service.delete_order(db, order)
