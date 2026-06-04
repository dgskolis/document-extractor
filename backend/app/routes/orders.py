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
from app.logging_context import generate_reference_id
from app.models.order import Order
from app.schemas.document import (
    DocumentUploadResponse,
    build_partial_extraction_detail,
    build_text_extraction_error_detail,
    build_upload_error_detail,
)
from app.schemas.order import OrderCreate, OrderListResponse, OrderResponse, OrderUpdate
from app.services import order_service
from app.services.upload_pipeline import PartialExtractionError, process_upload_sync
from app.upload_executor import run_upload_task

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
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    reference_id = generate_reference_id()
    try:
        return await run_upload_task(process_upload_sync, file, reference_id)
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=build_upload_error_detail(reference_id=reference_id),
        ) from exc
    except UnsupportedMediaTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=build_upload_error_detail(reference_id=reference_id),
        ) from exc
    except TextExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=build_text_extraction_error_detail(reference_id=reference_id),
        ) from exc
    except OpenAIConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=build_upload_error_detail(reference_id=reference_id),
        ) from exc
    except PatientExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=build_upload_error_detail(reference_id=reference_id),
        ) from exc
    except PartialExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=build_partial_extraction_detail(exc.extraction, reference_id=exc.reference_id),
        ) from exc


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
