from medkit.models import (
    ClinicalTrial,
    DrugInfo,
    ResearchPaper,
)


def build_drug_info(**kwargs) -> DrugInfo:
    default = {
        "brand_name": "TestDrug",
        "generic_name": "Test Generic",
        "manufacturer": "Test Pharma",
        "indications": ["Test Condition"],
        "warnings": ["Test Warning"],
        "purpose": ["Test Purpose"],
        "route": ["ORAL"],
    }
    default.update(kwargs)
    return DrugInfo(**default)  # type: ignore[arg-type]


def build_research_paper(**kwargs) -> ResearchPaper:
    default = {
        "pmid": "12345678",
        "title": "A Test Study on TestDrug",
        "abstract": "This is a test abstract.",
        "authors": ["Test, A."],
        "journal": "Journal of Test",
        "publication_date": "2023-01-01",
        "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        "doi": "10.1234/test.123",
    }
    default.update(kwargs)
    return ResearchPaper(**default)  # type: ignore[arg-type]


def build_clinical_trial(**kwargs) -> ClinicalTrial:
    default = {
        "nct_id": "NCT12345678",
        "title": "A Test Trial for TestDrug",
        "status": "RECRUITING",
        "conditions": ["Test Condition"],
        "description": "A detailed description.",
        "recruiting": True,
        "url": "https://clinicaltrials.gov/study/NCT12345678",
        "phase": ["PHASE1"],
        "location": ["Test City, USA"],
        "eligibility": "Adults 18+",
        "interventions": ["Test Intervention"],
    }
    default.update(kwargs)
    return ClinicalTrial(**default)  # type: ignore[arg-type]
