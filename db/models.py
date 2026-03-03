import uuid
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Date, Numeric, Integer,
    ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class ContractType(Base):
    __tablename__ = "contract_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20))
    sort_order = Column(Integer, default=0)

class ContractStatus(Base):
    __tablename__ = "contract_statuses"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    code = Column(String(20), nullable=False, unique=True)

class PaymentCondition(Base):
    __tablename__ = "payment_conditions"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

class Counterparty(Base):
    __tablename__ = "counterparties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    party_type = Column(String(10), nullable=False)  # 'legal' или 'individual'
    full_name = Column(String(255), nullable=False)
    short_name = Column(String(100))
    unp = Column(String(9), unique=True)
    legal_address = Column(Text)
    actual_address = Column(Text)
    postal_address = Column(Text)
    director_position = Column(String(150))
    director_full_name = Column(String(255))
    passport_series = Column(String(20))
    passport_issue_date = Column(Date)
    passport_issued_by = Column(Text)
    identification_number = Column(String(20))
    citizenship = Column(String(100))
    registration_address = Column(Text)
    actual_residence = Column(Text)
    client_type = Column(String(20))
    is_employee = Column(Boolean, default=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(party_type.in_(['legal', 'individual']), name='check_party_type'),
    )

    contact_persons = relationship("ContactPerson", back_populates="counterparty", cascade="all, delete-orphan")
    bank_accounts = relationship("BankAccount", back_populates="counterparty", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="counterparty")

class ContactPerson(Base):
    __tablename__ = "contact_persons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    counterparty_id = Column(UUID(as_uuid=True), ForeignKey("counterparties.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(255), nullable=False)
    position = Column(String(150))
    phone_work = Column(String(20))
    phone_mobile1 = Column(String(20))
    phone_mobile2 = Column(String(20))
    email1 = Column(String(100))
    email2 = Column(String(100))
    viber = Column(String(20))
    telegram = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    counterparty = relationship("Counterparty", back_populates="contact_persons")

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    counterparty_id = Column(UUID(as_uuid=True), ForeignKey("counterparties.id", ondelete="CASCADE"), nullable=False)
    bank_name = Column(String(255), nullable=False)
    bic = Column(String(11))
    account_number = Column(String(34), nullable=False)
    currency = Column(String(3), default="BYN")
    is_main = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    counterparty = relationship("Counterparty", back_populates="bank_accounts")

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_number = Column(String(50), nullable=False)
    post_number = Column(String(10), nullable=False)
    contract_type_id = Column(Integer, ForeignKey("contract_types.id"), nullable=False)
    counterparty_id = Column(UUID(as_uuid=True), ForeignKey("counterparties.id"), nullable=False)
    status_id = Column(Integer, ForeignKey("contract_statuses.id"), nullable=False)
    conclusion_date = Column(Date)
    place_of_conclusion = Column(String(255))
    validity_period_type = Column(String(10))  # 'date' or 'condition'
    expiry_date = Column(Date)
    estimated_completion_date = Column(Date)
    total_amount = Column(Numeric(12, 2))
    signed_by_contact_id = Column(UUID(as_uuid=True), ForeignKey("contact_persons.id"), nullable=True)
    signed_by_basis = Column(Text)
    file_link = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("contract_number", "post_number"),
        CheckConstraint(validity_period_type.in_(['date', 'condition']), name='check_validity_period_type'),
    )

    contract_type = relationship("ContractType")
    status = relationship("ContractStatus")
    counterparty = relationship("Counterparty", back_populates="contracts")
    signed_by = relationship("ContactPerson")
    stages = relationship("ContractStage", back_populates="contract", cascade="all, delete-orphan")

class ContractStage(Base):
    __tablename__ = "contract_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    stage_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    expected_result = Column(Text)
    confirmation_document = Column(String(255))
    payment_condition_id = Column(Integer, ForeignKey("payment_conditions.id"), nullable=False)
    prepayment_percent = Column(Numeric(5, 2))
    prepayment_days = Column(Integer)
    final_payment_days = Column(Integer)
    amount = Column(Numeric(12, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contract = relationship("Contract", back_populates="stages")
    payment_condition = relationship("PaymentCondition")