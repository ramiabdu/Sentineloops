from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.db import get_db
from app.repositories.accounts import get_account, list_accounts
from app.schemas.account import AccountCreate, AccountResponse
from app.services.accounts import AccountAlreadyExistsError, onboard_account

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> AccountResponse:
    try:
        account = onboard_account(db, payload)
    except AccountAlreadyExistsError as exc:
        raise ConflictError(
            code="account_already_exists",
            message="Cloud account is already onboarded.",
        ) from exc

    return AccountResponse.model_validate(account)


@router.get("", response_model=list[AccountResponse])
def get_accounts(db: Session = Depends(get_db)) -> list[AccountResponse]:
    return [AccountResponse.model_validate(account) for account in list_accounts(db)]


@router.get("/{account_id}", response_model=AccountResponse)
def get_account_by_id(account_id: UUID, db: Session = Depends(get_db)) -> AccountResponse:
    account = get_account(db, account_id)
    if account is None:
        raise NotFoundError(
            code="account_not_found",
            message="Cloud account was not found.",
        )

    return AccountResponse.model_validate(account)
