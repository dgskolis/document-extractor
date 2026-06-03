from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_order_or_404
from app.exceptions import (
    OpenAIConfigurationError,
    PatientExtractionError,
    TextExtractionError,
    UnsupportedMediaTypeError,
)
from app.models.order import Order
from app.schemas.document import (
    DocumentUploadResponse,
    build_partial_extraction_detail,
    is_extraction_complete,
)
from app.schemas.order import OrderCreate, OrderListResponse, OrderResponse, OrderUpdate
from app.services import document_service, order_service, patient_extraction_service

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

DEFAULT_LIST_LIMIT = 100
MAX_LIST_LIMIT = 1000


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)) -> OrderResponse:
    return order_service.create_order(db, order_in)


@router.get("/", response_model=OrderListResponse)
def list_orders(
    db: Session = Depends(get_db),
    limit: int = Query(default=DEFAULT_LIST_LIMIT, ge=1, le=MAX_LIST_LIMIT),
    offset: int = Query(default=0, ge=0),
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
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    content = file.file.read()

    try:
        document_text = document_service.extract_text(
            content,
            content_type=file.content_type,
            filename=file.filename,
        )
    except UnsupportedMediaTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type",
        ) from exc
    except TextExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unable to extract text from document",
        ) from exc

    try:
        extracted_fields = patient_extraction_service.extract_patient_fields(document_text)
    except OpenAIConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured",
        ) from exc
    except PatientExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Patient field extraction failed",
        ) from exc

    if not is_extraction_complete(extracted_fields):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=build_partial_extraction_detail(extracted_fields),
        )

    assert extracted_fields.first_name is not None
    assert extracted_fields.last_name is not None
    assert extracted_fields.date_of_birth is not None

    order_in = OrderCreate(
        patient_first_name=extracted_fields.first_name,
        patient_last_name=extracted_fields.last_name,
        date_of_birth=extracted_fields.date_of_birth,
    )
    order = order_service.create_order(db, order_in)
    return DocumentUploadResponse(extraction=extracted_fields, order=order)


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
