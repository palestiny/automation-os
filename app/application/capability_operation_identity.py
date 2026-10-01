from __future__ import annotations

from hashlib import sha256


def derive_capability_operation_id(
    execution_id: object,
    workflow_definition_id: object,
    step_index: int,
) -> str:
    if step_index < 0:
        raise ValueError("step_index cannot be negative")
    material = f"{execution_id}:{workflow_definition_id}:{step_index}".encode("utf-8")
    return sha256(material).hexdigest()
