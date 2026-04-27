from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.account import Account
from app.repositories.accounts import create_account, get_account_by_external_id
from app.schemas.account import AccountCreate


class AccountAlreadyExistsError(Exception):
    pass


def onboard_account(db: Session, payload: AccountCreate) -> Account:
    existing_account = get_account_by_external_id(
        db,
        cloud_provider=payload.cloud_provider,
        external_id=payload.external_id,
    )
    if existing_account is not None:
        raise AccountAlreadyExistsError()

    account = create_account(
        db,
        name=payload.name,
        cloud_provider=payload.cloud_provider,
        external_id=payload.external_id,
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AccountAlreadyExistsError from exc

    db.refresh(account)
    return account
