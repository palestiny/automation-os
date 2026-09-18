import pytest

from app.domain.reporting import ReportAsset, ReportSpecification


def test_report_specification_captures_report_definition():
    spec = ReportSpecification(
        title="Sales Report",
        metrics=("revenue", "orders"),
        filters={"region": "EG"},
    )

    assert spec.title == "Sales Report"
    assert spec.metrics == ("revenue", "orders")
    assert spec.filters["region"] == "EG"


def test_report_specification_rejects_empty_title():
    with pytest.raises(ValueError, match="title"):
        ReportSpecification("", ("revenue",), {})


def test_report_specification_rejects_duplicate_metrics():
    with pytest.raises(ValueError, match="unique"):
        ReportSpecification("Sales", ("revenue", "revenue"), {})


def test_report_asset_is_immutable():
    asset = ReportAsset("Sales", ({"revenue": 100},))

    with pytest.raises(AttributeError):
        asset.title = "Other"
