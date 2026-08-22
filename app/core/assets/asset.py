from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Asset:
    id: UUID
    type: str
    name: str
    location: str

    @staticmethod
    def create(
        asset_type: str,
        name: str,
        location: str,
    ) -> "Asset":
        return Asset(
            id=uuid4(),
            type=asset_type,
            name=name,
            location=location,
        )