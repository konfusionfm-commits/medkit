import pytest

from medkit.models import (
    ClinicalTrial,
    DrugInfo,
    InteractionWarning,
)


def test_drug_info_validation():
    drug = DrugInfo(
        brand_name="Brand",
        generic_name="Generic",
        manufacturer="Makers",
        indications=["Ind1", "Ind2"],
        interactions=[],
        dosage_form="Tablet",
        route=["Oral"],
    )
    assert drug.brand_name == "Brand"
    assert drug.generic_name == "Generic"


def test_clinical_trial_validation():
    trial = ClinicalTrial(
        nct_id="NCT00000000",
        title="Valid Trial",
        status="COMPLETED",
        conditions=["Cancer"],
        description="test",
        url="https://test.com",
        recruiting=False,
        phase=["PHASE1"],
        location=["US"],
        eligibility="Adults",
        interventions=["Drug"],
    )
    assert trial.nct_id == "NCT00000000"


def test_clinical_trial_null_nct_id():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ClinicalTrial(nct_id=None, title="Valid Trial", status="COMPLETED")


def test_interaction_warning_validation():
    warn = InteractionWarning(severity="High", risk="Bleeding", evidence="Some Trial Data")
    assert warn.severity == "High"
    assert warn.risk == "Bleeding"
    assert warn.evidence == "Some Trial Data"
