# 🏥 MedKit: A Unified Platform for Medical Data APIs

[![CI Status](https://img.shields.io/badge/CI-passing-success)](https://github.com/interestng/medkit/actions)
[![Test Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen.svg)](https://github.com/interestng/medkit/actions)
[![Strict Mypy](https://img.shields.io/badge/typing-Strict-blue.svg)](https://mypy.readthedocs.io/en/stable/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-3.0.0-orange)](https://pypi.org/project/medkit-sdk/)

MedKit is a high-performance, unified SDK that transforms fragmented medical APIs into a single, programmable platform. It provides a clean interface for **OpenFDA**, **PubMed**, and **ClinicalTrials.gov**, augmented with a clinical intelligence layer and relationship mapping.

> [!IMPORTANT]
> **v3.0.0 Release**: This major update transforms MedKit into a production-grade SDK. It introduces robust connection pooling, dynamic rate limiting, circuit breakers, exponential jitter retries, strict strict MyPy types, and completely formalized Pydantic V2 validations spanning a `39/39` passing test suite.

![MedKit CLI Demo](demo.gif)

---

## ✨ Async Example (v3.0.0)

```python
import asyncio
from medkit import AsyncMedKit

async def main():
    async with AsyncMedKit() as med:
        # Unified search across all providers in parallel
        results = await med.search("pembrolizumab")
        
        print(f"Drugs found: {len(results.drugs)}")
        print(f"Clinical Trials: {len(results.trials)}")
        
        # Get a synthesized conclusion
        conclusion = await med.ask("What is the clinical status of Pembrolizumab for NSCLC?")
        print(f"Summary: {conclusion.summary}")
        print(f"Confidence: {conclusion.confidence_score}")

asyncio.run(main())
```

---

## 🤔 Why MedKit?

| Feature | Without MedKit | With MedKit |
| :--- | :--- | :--- |
| **Integrations** | 3 separate APIs / SDKs | **Unified** Sync/Async Client |
| **Resilience** | 403 blocks from gov APIs | **Auto-Fallback** (Curl/v2 API) |
| **Synthesis** | Alphabetical/Noisy lists | **Frequency-Ranked** Intervals |
| **Logic** | Manual data correlation | Native **knowledge graphs** |
| **Speed** | Sequential network calls | **Parallel** Async Orchestration |

---
Note: This is still a Work in Progress, meaning there might be missing functionaliy, placeholders, etc. If you find something that you would like to be fixed/implemented soon, please open an issue. Also, this SDK is not FDA-Approved, and has no official medical licensing. Use at your own discretion!

## 🏗️ Architecture

MedKit abstracts complexity through a high-performance orchestration layer:

```text
      Developer / User
             │
             ▼
    ┌───────────────────┐
    │  MedKit / Async   │ (Unified Interface)
    └─────────┬─────────┘
              │
    ┌─────────┴─────────────────────┐
    │       Intelligence Layer      │
    │  ├─ Ask Engine (Extraction)   │
    │  ├─ Graph Engine (Context)    │
    │  ├─ Interaction Engine        │
    │  └─ Synthesis Engine (Ranked) │
    └─────────┬─────────────────────┘
              │
    ┌─────────┴─────────────────────┐
    │       Providers Layer         │
    │  ├─ OpenFDA     (Drug Label)  │
    │  ├─ PubMed      (Research)    │
    │  └─ ClinTrials  (v2 + Fallback)│
    └───────────────────────────────┘
```

---

## 🚀 Core Platform Features

- **Robust Connectivity (NEW)**: Automatic `curl` fallback for ClinicalTrials.gov bypasses TLS fingerprinting blocks, ensuring 100% data availability.
- **Enterprise Reliability**: Embedded exponential backoff retries with full jitter, circuit breakers preventing upstream cascades, and sliding-window rate limiters.
- **Strictly Typed Ecosystem**: Zero `Any` leakage. 100% strictly typed `medkit/py.typed` interface enforcing strict Pydantic V2 `extra="forbid"` models natively.
- **Async-First Orchestration**: Parallel health checks and search execution eliminate latency bottlenecks and perceived "hangs."
- **Precision Evidence Synthesis**: Automated clinical verdicts with frequency-ranked interventions and filtered therapeutic agents (Drugs/Biologicals).
- **High-Performance CLI**: Interactive, list-based visualization for trials and research papers, optimized for all terminal sizes.
- **Unified Caching**: Enhanced Disk and Memory caching for high-performance repeat queries.

---

## 🛠️ Testing

MedKit ships with a production-grade, isolated mock testing infrastructure that achieves comprehensive validation without relying on live API stability.

```bash
pytest tests/ -v
```

---

## 📦 Installation

```bash
pip install medkit-sdk
```

---

## 🖥️ CLI Power Tools

### Clinical Ask (Synthesized)
```bash
$ medkit ask "pembrolizumab for lung cancer"

 Clinical Conclusion 

Summary: Highly-validated therapeutic landscape with multi-modal evidence.
Evidence Confidence: [████████████████████] 1.00

Top Interventions: Pembrolizumab, Bevacizumab, Carboplatin, Cisplatin
```

### Trials Search
```bash
$ medkit trials "melanoma" --limit 5

Clinical Trials for 'melanoma'
- NCT01234567: RECRUITING - Study of Pembrolizumab in Advanced Melanoma
- NCT07654321: COMPLETED - Comparison of B-Raf Inhibitors
```

### Knowledge Graph
```bash
$ medkit graph "lung cancer"

Knowledge Graph: lung cancer
Nodes: 26 | Edges: 8

 Lung Cancer 
├── Drugs
│   └── None found
├── Trials
│   ├── A Study of QL1706 Combined Wit...
│   ├── Circulating Tumor DNA Detectio...
│   └── Trial of Single Protein Encaps...
└── Papers
    ├── Phase III placebo-controlled o...
    └── Therapeutic strategies for eld...
```

## 🤝 Contributing

We welcome contributions! As an open-source project, community feedback and improvements can be the backbone of thi.

1. **Check the Code**: Feel free to dive into the codebase and identify any bugs or areas for improvement.
2. **Open an Issue**: If you find a fault, no matter how small, please open an issue or start a discussion.
3. **Submit a Pull Request**: Direct improvements and new provider integrations are highly encouraged.

I'd much rather have a brutal code review that helps me improve the engine than silence!

---

## 🗺️ Roadmap

- [x] **v1.0.0**: Foundation medical mesh and provider integration.
- [x] **v2.0.0**: Async architecture, v2 API support.
- [x] **v3.0.0**: Major revamp: Large-scale readiness (Circuit Breakers, Retries, Coverage, Pydantic V2, CLI UI).
- [ ] **v4.0.0**: Local GraphQL medical mesh endpoint.

---

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.
