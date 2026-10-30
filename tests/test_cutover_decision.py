from fieldservice_models import DispatchStatus
from tenant_cutover_service import decide_follow_up_status


def test_dispatched_without_photos_requires_technician_follow_up() -> None:
    result = decide_follow_up_status(
        dispatch_status=DispatchStatus.DISPATCHED,
        photo_count=0,
    )
    assert result == "technician_follow_up_required"
