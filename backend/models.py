from sqlalchemy import Boolean, Column, Integer, String, Date, DateTime, JSON, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(String(30), unique=True, nullable=False, index=True)  # the ID people sign in with
    password_hash = Column(String(255), nullable=False)
    plain_password = Column(String(255), nullable=True)  # stored for Super Admin view (except mutual super admin)
    is_admin = Column(Boolean, nullable=False, server_default='0', default=False)  # kept in sync with role
    role = Column(String(10), nullable=False, server_default='limited', default='limited')  # admin | standard | limited
    permissions = Column(JSON, nullable=True)  # granular page and action permissions
    token_version = Column(Integer, nullable=False, server_default='0', default=0)  # bump = sign out everywhere
    created_at = Column(TIMESTAMP, server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False, index=True)
    avatar = Column(Text, nullable=True)  # an emoji, or a small photo stored as a data-URL
    created_at = Column(TIMESTAMP, server_default=func.now())
    deleted_at = Column(DateTime, nullable=True, index=True)  # set = customer is in the bin
    deleted_by = Column(String(30), nullable=True)


class Device(Base):
    __tablename__ = "sim_devices"  # new name: the database already has an older, different "devices" table

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    device_sr_no = Column(String(50), index=True)
    imei = Column(String(20), unique=True, nullable=False, index=True)
    iccid = Column(String(30), index=True)
    msisdn1 = Column(String(20), index=True)
    msisdn2 = Column(String(20))
    act_date = Column(Date)
    expiry_date = Column(Date, index=True)
    dispatched_date = Column(Date)
    model = Column(String(100))
    sim_provider = Column(String(100), index=True)
    activation_plan = Column(String(100))
    firmware = Column(String(100))
    flash = Column(String(100))
    sim_type = Column(String(20))  # "E-SIM" or "Plastic SIM"
    added_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Recycle bin: a deleted record keeps its row and just gets these filled in.
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by = Column(String(30), nullable=True)
    delete_reason = Column(String(200), nullable=True)

    extra = Column(JSON, nullable=True)  # any extra CSV columns: {"Plan": "Gold", ...}

    customer = relationship("Customer")


class ColumnRegistry(Base):
    """Names of the extra columns seen in uploads, so new columns appear in the table by themselves."""
    __tablename__ = "sim_column_registry"  # new name: an older, different "column_registry" table already exists

    name = Column(String(100), primary_key=True)


class ActivityLog(Base):
    """Who signed in and what they did. No foreign key on purpose: history must survive deleting a user."""
    __tablename__ = "sim_activity_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    user_login = Column(String(30), nullable=False, default="", index=True)
    user_name = Column(String(100), nullable=False, default="")
    action = Column(String(30), nullable=False, index=True)
    detail = Column(String(500), nullable=False, default="")
    ip = Column(String(45), nullable=False, default="")
    created_at = Column(DateTime, nullable=False, index=True)  # UTC


class ErroredRecord(Base):
    """Holds upload entries that had errors so users can review, edit/upload to customer, or move to cart."""
    __tablename__ = "sim_errored_records"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(150), nullable=True)
    imei = Column(String(100), nullable=True)
    device_sr_no = Column(String(100), nullable=True)
    iccid = Column(String(100), nullable=True)
    msisdn1 = Column(String(100), nullable=True)
    msisdn2 = Column(String(100), nullable=True)
    act_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    dispatched_date = Column(Date, nullable=True)
    model = Column(String(150), nullable=True)
    sim_provider = Column(String(150), nullable=True)
    activation_plan = Column(String(150), nullable=True)
    firmware = Column(String(150), nullable=True)
    flash = Column(String(150), nullable=True)
    sim_type = Column(String(100), nullable=True)
    extra = Column(JSON, nullable=True)
    error_reason = Column(String(500), nullable=False, default="Invalid entry")
    created_at = Column(TIMESTAMP, server_default=func.now())

