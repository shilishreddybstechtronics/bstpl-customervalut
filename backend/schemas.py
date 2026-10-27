import re
from datetime import date, datetime, timedelta
from typing import Optional

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, AliasChoices

ID_PATTERN = r"^[A-Za-z0-9_.-]{3,30}$"
Role = Literal["admin", "standard", "limited"]


_DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y/%m/%d", "%d-%b-%Y", "%d %b %Y",
                 "%d-%b-%y", "%d/%m/%y", "%d-%m-%y", "%b %d, %Y",
                 "%d-%B-%Y", "%d-%B-%y", "%d %B %Y", "%B %d, %Y")


def _to_date(v):
    """Accepts what real spreadsheets contain: blanks, Excel serial numbers, 2025-03-01 05:30:00, 01-03-2025 (day first).
    If a date cannot be parsed, safely ignore that particular value and return None instead of raising an error."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    if not s or s.lower() in ("nan", "nat", "none", "null", "-", "--", "#n/a", "n/a", "na", "nil", "undefined"):
        return None
    try:
        n = float(s)
    except ValueError:
        n = None
    if n is not None:
        if n == 0:  # Excel shows an empty date cell as 0
            return None
        if 20000 < n < 80000:  # Excel serial day number
            return date(1899, 12, 30) + timedelta(days=int(n))
        return None
    s = re.split(r"[T ]\d{1,2}:\d{2}", s)[0].strip()  # drop any time part
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _pw_ok(v):
    # bcrypt only handles 72 BYTES; emoji and accented letters take more than one byte each
    if v is not None and len(v.encode()) > 72:
        raise ValueError("Password is too long (72 bytes at most; emoji and accented letters count as several).")
    return v


def _clean_str_val(v):
    if v is None:
        return None
    s = str(v).strip()
    if s.lower() in ("nan", "none", "null", "undefined"):
        return None
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s


def _clean_iccid_val(v):
    if v is None:
        return None
    s = str(v).strip()
    if s.lower() in ("nan", "none", "null", "undefined"):
        return None
    if re.search(r"e\+", s, re.I):
        try:
            s = str(int(float(s)))
        except Exception:
            pass
    if s.endswith(".0"):
        s = s[:-2]
    s = re.sub(r"[\s\-_]+", "", s)
    return s.strip().upper()


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    user_id: str = Field(pattern=ID_PATTERN)
    password: str = Field(min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return _pw_ok(v)


class LoginIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=30)
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: int
    name: str
    user_id: str
    is_admin: bool = False
    role: str = "limited"
    category: Optional[str] = None
    category_label: Optional[str] = None
    badge: Optional[str] = None
    is_master: Optional[bool] = False
    can_delete: Optional[bool] = False
    password: Optional[str] = None
    permissions: Optional[dict[str, bool]] = None

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- customers and devices ----
class DeviceIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    customer_name: str = Field("", max_length=255)
    imei: str = Field("", max_length=100)
    device_sr_no: Optional[str] = Field(None, max_length=150)
    iccid: Optional[str] = Field(None, validation_alias=AliasChoices("iccid", "ccid", "ICCID", "CCID", "Iccid", "Ccid"), max_length=100)
    msisdn1: Optional[str] = Field(None, max_length=100)
    msisdn2: Optional[str] = Field(None, max_length=100)
    act_date: Optional[date] = None
    expiry_date: Optional[date] = None  # if empty, defaults to act_date + 365 days
    extra: Optional[dict[str, Optional[str]]] = None  # any additional columns from the upload
    model: Optional[str] = Field(None, max_length=150)
    sim_provider: Optional[str] = Field(None, max_length=150)
    activation_plan: Optional[str] = Field(None, max_length=150)
    firmware: Optional[str] = Field(None, max_length=150)
    flash: Optional[str] = Field(None, max_length=150)
    sim_type: Optional[str] = Field(None, max_length=100)
    dispatched_date: Optional[date] = None

    @field_validator("iccid", mode="before")
    @classmethod
    def _clean_iccid(cls, v):
        return _clean_iccid_val(v)

    @field_validator("customer_name", "imei", "device_sr_no", "msisdn1", "msisdn2",
                     "model", "sim_provider", "activation_plan", "firmware", "flash", "sim_type", mode="before")
    @classmethod
    def _clean_str(cls, v):
        return _clean_str_val(v) or "" if cls == "customer_name" or cls == "imei" else _clean_str_val(v)

    @field_validator("act_date", "expiry_date", "dispatched_date", mode="before")
    @classmethod
    def _dates(cls, v):
        return _to_date(v)


class DeviceUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    customer_name: Optional[str] = Field(None, min_length=1, max_length=255)
    device_sr_no: Optional[str] = Field(None, max_length=150)
    iccid: Optional[str] = Field(None, validation_alias=AliasChoices("iccid", "ccid", "ICCID", "CCID", "Iccid", "Ccid"), max_length=100)
    msisdn1: Optional[str] = Field(None, max_length=100)
    msisdn2: Optional[str] = Field(None, max_length=100)
    act_date: Optional[date] = None
    expiry_date: Optional[date] = None
    extra: Optional[dict[str, Optional[str]]] = None
    model: Optional[str] = Field(None, max_length=150)
    sim_provider: Optional[str] = Field(None, max_length=150)
    activation_plan: Optional[str] = Field(None, max_length=150)
    firmware: Optional[str] = Field(None, max_length=150)
    flash: Optional[str] = Field(None, max_length=150)
    sim_type: Optional[str] = Field(None, max_length=100)
    dispatched_date: Optional[date] = None

    @field_validator("iccid", mode="before")
    @classmethod
    def _clean_iccid(cls, v):
        return _clean_iccid_val(v)

    @field_validator("device_sr_no", "msisdn1", "msisdn2",
                     "model", "sim_provider", "activation_plan", "firmware", "flash", "sim_type", mode="before")
    @classmethod
    def _clean_str(cls, v):
        return _clean_str_val(v)

    @field_validator("act_date", "expiry_date", "dispatched_date", mode="before")
    @classmethod
    def _dates(cls, v):
        return _to_date(v)


class BulkIn(BaseModel):
    rows: list[DeviceIn] = Field(max_length=20000)  # the page sends 1,000-2,000 at a time; this is only a safety ceiling
    mode: Optional[Literal["skip", "replace"]] = "skip"
    direct_empty: Optional[bool] = False


class SimDataRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    imei: Optional[str] = Field(None, max_length=100)
    iccid: str = Field("", validation_alias=AliasChoices("iccid", "ccid", "ICCID", "CCID", "Iccid", "Ccid"), max_length=100)
    msisdn1: Optional[str] = Field(None, max_length=100)
    msisdn2: Optional[str] = Field(None, max_length=100)
    sim_provider: Optional[str] = Field(None, max_length=150)
    model: Optional[str] = Field(None, max_length=150)
    activation_plan: Optional[str] = Field(None, max_length=150)
    firmware: Optional[str] = Field(None, max_length=150)
    flash: Optional[str] = Field(None, max_length=150)
    sim_type: Optional[str] = Field(None, max_length=100)
    act_date: Optional[date] = None
    expiry_date: Optional[date] = None

    @field_validator("iccid", mode="before")
    @classmethod
    def _clean_iccid(cls, v):
        return _clean_iccid_val(v) or ""

    @field_validator("imei", "msisdn1", "msisdn2", "sim_provider", "model", "activation_plan", "firmware", "flash", "sim_type", mode="before")
    @classmethod
    def _clean_str(cls, v):
        return _clean_str_val(v) or ""

    @field_validator("act_date", "expiry_date", mode="before")
    @classmethod
    def _dates(cls, v):
        return _to_date(v)


class SimDataCheckIn(BaseModel):
    rows: list[SimDataRow] = Field(max_length=50000)
    match_by: Optional[str] = "iccid"
    overwrite: bool = True
    sim_provider: Optional[str] = None

    @field_validator("match_by", mode="before")
    @classmethod
    def _norm_match_by(cls, v):
        if not v:
            return "iccid"
        s = str(v).strip().lower()
        if s in ("iccid", "ccid"):
            return "iccid"
        return s


class SimDataApplyIn(BaseModel):
    rows: list[SimDataRow] = Field(max_length=50000)
    match_by: Optional[str] = "iccid"
    overwrite: bool = True
    sim_provider: Optional[str] = None

    @field_validator("match_by", mode="before")
    @classmethod
    def _norm_match_by(cls, v):
        if not v:
            return "iccid"
        s = str(v).strip().lower()
        if s in ("iccid", "ccid"):
            return "iccid"
        return s


class BulkFetchIn(BaseModel):
    queries: list[str] = Field(max_length=100000)
    field: Optional[str] = "all"
    customer_id: Optional[int] = None
    sim_type: Optional[str] = "all"

    @field_validator("field", mode="before")
    @classmethod
    def _norm_field(cls, v):
        if not v:
            return "all"
        s = str(v).strip().lower()
        if s in ("iccid", "ccid"):
            return "iccid"
        return s


class AddColumnIn(BaseModel):
    column_name: str = Field(min_length=1, max_length=100)
    target: Literal["all", "customer", "specified"] = "all"
    customer_id: Optional[int] = None
    imeis: Optional[list[str]] = None
    value: Optional[str] = None


class DeleteColumnIn(BaseModel):
    column_name: str = Field(min_length=1, max_length=100)


class ExportIn(BaseModel):
    title: Optional[str] = "Export"
    headers: list[str]
    rows: list[list[Optional[str]]]


class CustomerIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class ReasonIn(BaseModel):
    reason: Optional[str] = Field(None, max_length=200)


# ---- password and user management ----
class PasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=64)

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, v):
        return _pw_ok(v)


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    user_id: str = Field(pattern=ID_PATTERN)
    password: str = Field(min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return _pw_ok(v)
    role: Optional[Role] = None       # new
    is_admin: bool = False            # old field, still accepted: used only when role is not given
    permissions: Optional[dict[str, bool]] = None


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[Role] = None
    is_admin: Optional[bool] = None   # old field, used only when role is not given
    password: Optional[str] = Field(None, min_length=8, max_length=64)  # admin password reset
    permissions: Optional[dict[str, bool]] = None

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return _pw_ok(v)


class UserNameUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class PermissionsUpdate(BaseModel):
    permissions: dict[str, bool]


# ---- customer management ----
class CustomerRename(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class RenameItem(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=150)


class RenameAllIn(BaseModel):
    renames: list[RenameItem] = Field(min_length=1, max_length=500)


class AvatarIn(BaseModel):
    avatar: Optional[str] = Field(None, max_length=60000)  # emoji or "data:image/...;base64,..." (empty = remove)


class MergeIn(BaseModel):
    target_id: int


# ---- errored records ----
class ErroredRecordIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    customer_name: Optional[str] = None
    imei: Optional[str] = None
    device_sr_no: Optional[str] = None
    iccid: Optional[str] = None
    msisdn1: Optional[str] = None
    msisdn2: Optional[str] = None
    act_date: Optional[date] = None
    expiry_date: Optional[date] = None
    dispatched_date: Optional[date] = None
    model: Optional[str] = None
    sim_provider: Optional[str] = None
    activation_plan: Optional[str] = None
    firmware: Optional[str] = None
    flash: Optional[str] = None
    sim_type: Optional[str] = None
    extra: Optional[dict[str, Optional[str]]] = None
    error_reason: str = "Invalid or unparseable data"

    @field_validator("act_date", "expiry_date", "dispatched_date", mode="before")
    @classmethod
    def _dates(cls, v):
        return _to_date(v)


class BulkErrorsIn(BaseModel):
    records: list[ErroredRecordIn]

