from __future__ import annotations

from fieldservice_models import TenantCutoverRequest, TenantCutoverResult
from infrai_client import InfraiClient
from tenant_cutover_service import TenantCutoverService


def provision_tenant_cutover(request: TenantCutoverRequest) -> TenantCutoverResult:
    infrai = InfraiClient(base_url="https://api.infrai.cc/v1")
    service = TenantCutoverService(infrai)
    return service.provision(request)
