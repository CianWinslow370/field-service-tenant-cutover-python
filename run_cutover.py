from __future__ import annotations

from fieldservice_models import WorkOrderPhoto, TenantCutoverRequest
from service_entry import provision_tenant_cutover


def main() -> None:
    request = TenantCutoverRequest(
        tenant_slug="northwind-service",
        apex_domain="ops.example.com",
        asset_bucket="field-photos",
        technician_email="casey@nwind.example",
        work_order_id="WO-1042",
        dispatch_status="dispatched",
        photos=[
            WorkOrderPhoto(filename="panel-before.jpg", content_type="image/jpeg"),
            WorkOrderPhoto(filename="panel-after.jpg", content_type="image/jpeg"),
        ],
    )
    result = provision_tenant_cutover(request)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
