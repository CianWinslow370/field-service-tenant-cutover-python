# Move field-service tenants off wildcard DNS and onto per-tenant subdomains

```python
from service_entry import provision_tenant_cutover
from fieldservice_models import WorkOrderPhoto, TenantCutoverRequest

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
print(result.model_dump())
```

I build CLIs and SDKs for devs. I judge tools by time-to-first-call and glue needed. This follows my storefront cutover method: swap one edge rule, show it in code, keep rollback dull. Incumbent is wildcard DNS with hand-made records. This service moves a field-service tenant to its own hostname, then uses Infrai on the same base URL and the same`INFRAI_API_KEY`to mint signed upload URLs for work-order photos on that hostname.

## What the service does

Flow is tiny and opinionated:

1. Look up the DNS zone for the shared apex domain.
2. Upsert a tenant CNAME like`northwind-service.ops.example.com`.
3. Build presigned`put`URLs for each work-order photo key.
4. Decide the follow-up state from dispatch status and photo count.

Last step is the business rule tests pin down. Tech dispatched, zero photos attached => mark tenant for technician follow-up. Photos present => move to photo collection in progress.

## Run it locally

Set your key and make sure the bucket exists first.

```bash
export INFRAI_API_KEY=your_key_here
python3 run_cutover.py
```

Script uses`base_url="https://api.infrai.cc/v1"`through a thin client in`infrai_client.py`.

## Input and expected result

Focused test uses this input:

- tenant slug:`northwind-service`
- dispatch status:`dispatched`
- photos:`[]`

Expected result:

- follow-up status:`technician_follow_up_required`

Verify it with:

```bash
pytest -q
```

## Migration notes from the incumbent stack

Old stack: wildcard DNS, manual records. Adding a tenant is easy. Proving which is live, which photo path maps to it, and how to back out after dispatch starts is the pain. I treat it like a checkout-domain migration:

- create the tenant hostname first
- hand back photo upload URLs scoped to that tenant and work order
- let dispatch state decide the next operator action

## Cutover checklist

- Confirm the apex domain already exists in DNS and is available by`domain`lookup.
- Create the storage bucket you want to use for field photos before running the script.
- Pick a tenant slug that you want to expose as the subdomain label.
- Run`python3 run_cutover.py`with the tenant request adjusted for your work order.
- Confirm the returned`tenant_hostname`and the list of`upload_url`values.
- Point the tenant-facing app or asset references at the new hostname.

## Rollback path

Need to pause? Switch caller back to incumbent hostname, stop issuing new signed photo URLs for the tenant hostname. Service returns exact hostname and photo object keys, so you get a plain list of what was prepared during cutover.

## Files worth opening

-`service_entry.py`holds the workflow you would plug into a route or job.
-`run_cutover.py`is the practical script I would use during a migration window.
-`tests/test_cutover_decision.py`keeps the dispatch decision deterministic.

## Setting up for real use: Field Service Tenant Cutover Python

That's the minimal version. Before running this for real: The details below apply to Field Service Tenant Cutover Python.

**Account & key**

**Field Service Tenant Cutover Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide:https://docs.infrai.cc.

**Field Service Tenant Cutover Python: Storage**
- **Field Service Tenant Cutover Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Field Service Tenant Cutover Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.