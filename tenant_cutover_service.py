from __future__ import annotations

from typing import List

from fieldservice_models import (
    DispatchStatus,
    PhotoUploadInstruction,
    TenantCutoverRequest,
    TenantCutoverResult,
)
from infrai_client import InfraiClient


class TenantCutoverService:
    def __init__(self, infrai: InfraiClient) -> None:
        self.infrai = infrai

    def provision(self, request: TenantCutoverRequest) -> TenantCutoverResult:
        tenant_hostname = f"{request.tenant_slug}.{request.apex_domain}"
        zone = self.infrai.dns_domain_get(request.apex_domain)
        zone_data = zone["data"]
        zone_id = zone_data["zone_id"]

        self.infrai.dns_record_upsert(
            zone_id=zone_id,
            record_type="CNAME",
            name=request.tenant_slug,
            content=request.apex_domain,
            ttl=300,
            proxied=False,
            metadata={
                "tenant_slug": request.tenant_slug,
                "work_order_id": request.work_order_id,
            },
        )

        uploads: List[PhotoUploadInstruction] = []
        for photo in request.photos:
            object_key = f"tenants/{request.tenant_slug}/work-orders/{request.work_order_id}/{photo.filename}"
            presigned = self.infrai.storage_object_presign(
                bucket=request.asset_bucket,
                key=object_key,
                op="put",
                expires_seconds=900,
                content_type=photo.content_type,
                max_bytes=10_000_000,
                idempotency_key=f"{request.tenant_slug}:{request.work_order_id}:{photo.filename}",
            )
            uploads.append(
                PhotoUploadInstruction(
                    object_key=object_key,
                    upload_url=presigned["data"]["url"],
                    content_type=photo.content_type,
                )
            )

        follow_up_status = decide_follow_up_status(
            dispatch_status=request.dispatch_status,
            photo_count=len(request.photos),
        )

        return TenantCutoverResult(
            tenant_hostname=tenant_hostname,
            dns_record_name=request.tenant_slug,
            dispatch_status=request.dispatch_status,
            follow_up_status=follow_up_status,
            upload_instructions=uploads,
        )


def decide_follow_up_status(dispatch_status: DispatchStatus, photo_count: int) -> str:
    if dispatch_status == DispatchStatus.DISPATCHED and photo_count == 0:
        return "technician_follow_up_required"
    if dispatch_status == DispatchStatus.DISPATCHED and photo_count > 0:
        return "photo_collection_in_progress"
    if dispatch_status == DispatchStatus.COMPLETE and photo_count > 0:
        return "ready_for_review"
    return "awaiting_dispatch"
