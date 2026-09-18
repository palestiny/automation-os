from app.application.capability import Capability
from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext
from app.domain.business_reporting import BusinessData, ReportAsset, ReportSpecification


class InMemoryBusinessReportCapability(Capability):
    """Deterministic reporting capability used to prove the domain boundary."""

    id = "generate_business_report"

    def execute(self, context: ExecutionContext) -> CapabilityResult:
        try:
            data = context.get("business_data")
            specification = context.get("report_specification")
        except KeyError:
            return CapabilityResult.failure(
                "business_data and report_specification are required"
            )

        if not isinstance(data, BusinessData):
            return CapabilityResult.failure("business_data is required")
        if not isinstance(specification, ReportSpecification):
            return CapabilityResult.failure("report_specification is required")

        reference = f"memory://business-report/{specification.name}"
        asset = ReportAsset.create(specification, reference)
        context.set("report_asset", asset)

        return CapabilityResult.success()
