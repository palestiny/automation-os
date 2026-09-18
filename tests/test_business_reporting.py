import pytest
from app.domain.business_reporting import BusinessData, ReportAsset, ReportSpecification

def test_business_data_requires_values():
    with pytest.raises(ValueError):
        BusinessData.create({})

def test_business_data_copies_input():
    values = {"revenue": 100}
    data = BusinessData.create(values)
    values["revenue"] = 200
    assert data.values["revenue"] == 100

def test_report_specification_requires_name_and_format():
    with pytest.raises(ValueError):
        ReportSpecification.create("", "json")
    with pytest.raises(ValueError):
        ReportSpecification.create("Sales", "")

def test_report_asset_requires_valid_specification_and_reference():
    spec = ReportSpecification.create("Sales", "json")
    asset = ReportAsset.create(spec, "memory://report/1")
    assert asset.specification == spec
    assert asset.reference == "memory://report/1"
