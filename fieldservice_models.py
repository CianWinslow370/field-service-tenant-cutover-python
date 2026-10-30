from __future__ import annotations

from enum import Enum
import json
from dataclasses import asdict, dataclass, field
from typing import List


class _Model:
    def model_dump(self) -> dict:
        return asdict(self)

    def model_dump_json(self, *, indent: int | None = None) -> str:
        return json.dumps(self.model_dump(), indent=indent)


class DispatchStatus(str, Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    COMPLETE = "complete"


@dataclass
class WorkOrderPhoto(_Model):
    filename: str
    content_type: str

    def __post_init__(self) -> None:
        value = self.filename
        if not value or "/" in value or value.startswith("."):
            raise ValueError("filename must be a plain file name")


@dataclass
class TenantCutoverRequest(_Model):
    tenant_slug: str
    apex_domain: str
    asset_bucket: str
    technician_email: str
    work_order_id: str
    dispatch_status: DispatchStatus
    photos: List[WorkOrderPhoto] = field(default_factory=list)

    def __post_init__(self) -> None:
        value = self.tenant_slug
        if not 3 <= len(value) <= 63:
            raise ValueError("tenant_slug must be between 3 and 63 characters")
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
        if any(ch not in allowed for ch in value):
            raise ValueError("tenant_slug must use lowercase letters, digits, and hyphens")
        if value.startswith("-") or value.endswith("-"):
            raise ValueError("tenant_slug cannot start or end with a hyphen")


@dataclass
class PhotoUploadInstruction(_Model):
    object_key: str
    upload_url: str
    content_type: str


@dataclass
class TenantCutoverResult(_Model):
    tenant_hostname: str
    dns_record_name: str
    dispatch_status: DispatchStatus
    follow_up_status: str
    upload_instructions: List[PhotoUploadInstruction]
