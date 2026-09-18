from app.application.execution_context import ExecutionContext
from app.domain.business_reporting import BusinessData, ReportAsset, ReportSpecification
from app.infrastructure.capabilities.business_reporting import InMemoryBusinessReportCapability

def test_business_report_capability_produces_report_asset():
    context = ExecutionContext()
    context.set("business_data", BusinessData.create({"revenue": 100}))
    context.set("report_specification", ReportSpecification.create("Sales", "json"))

    result = InMemoryBusinessReportCapability().execute(context)

    assert result.succeeded
    assert isinstance(context.get("report_asset"), ReportAsset)

def test_business_report_capability_rejects_missing_data():
    result = InMemoryBusinessReportCapability().execute(ExecutionContext())
    assert not result.succeeded
