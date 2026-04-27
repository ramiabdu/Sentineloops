import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base
from app.models.account import AccountStatus, CloudProvider
from app.repositories.accounts import get_account, list_accounts
from app.schemas.account import AccountCreate
from app.services.accounts import AccountAlreadyExistsError, onboard_account


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        yield session


def test_onboard_account_creates_pending_account(db_session: Session):
    payload = AccountCreate(
        name="AWS production",
        cloud_provider=CloudProvider.AWS,
        external_id="123456789012",
    )

    account = onboard_account(db_session, payload)

    assert account.id is not None
    assert account.name == "AWS production"
    assert account.cloud_provider == CloudProvider.AWS
    assert account.external_id == "123456789012"
    assert account.status == AccountStatus.PENDING


def test_onboard_account_rejects_duplicate_provider_external_id(db_session: Session):
    payload = AccountCreate(
        name="AWS production",
        cloud_provider=CloudProvider.AWS,
        external_id="123456789012",
    )

    onboard_account(db_session, payload)

    with pytest.raises(AccountAlreadyExistsError):
        onboard_account(db_session, payload)


def test_account_repository_lists_and_fetches_accounts(db_session: Session):
    payload = AccountCreate(
        name="GCP security",
        cloud_provider=CloudProvider.GCP,
        external_id="gcp-project-1",
    )
    account = onboard_account(db_session, payload)

    accounts = list_accounts(db_session)

    assert accounts == [account]
    assert get_account(db_session, account.id) == account
