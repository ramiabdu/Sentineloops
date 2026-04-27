from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account, AccountStatus, CloudProvider


def create_account(
    db: Session,
    *,
    name: str,
    cloud_provider: CloudProvider,
    external_id: str,
    status: AccountStatus = AccountStatus.PENDING,
) -> Account:
    account = Account(
        name=name,
        cloud_provider=cloud_provider,
        external_id=external_id,
        status=status,
    )
    db.add(account)
    return account


def get_account(db: Session, account_id: UUID) -> Account | None:
    return db.get(Account, account_id)


def get_account_by_external_id(
    db: Session,
    *,
    cloud_provider: CloudProvider,
    external_id: str,
) -> Account | None:
    statement = select(Account).where(
        Account.cloud_provider == cloud_provider,
        Account.external_id == external_id,
    )
    return db.execute(statement).scalar_one_or_none()


def list_accounts(db: Session) -> list[Account]:
    statement = select(Account).order_by(Account.created_at.desc())
    return list(db.execute(statement).scalars().all())
