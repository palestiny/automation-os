# Project Structure

```text
app/
├── api/                 # HTTP/API adapters
├── application/        # use cases and orchestration
├── core/
│   ├── assets/          # asset-related core concepts
│   ├── capabilities/    # capability/plugin abstractions
│   ├── workflow/        # workflow construction/support
│   ├── dependencies.py
│   └── job_manager.py
├── domain/              # business domain
├── models/              # operational/data models
├── schemas/             # API/request/response schemas
├── services/            # infrastructure/provider services
└── main.py              # application composition/root

docs/
├── 00-Project Charter/
├── 00-Vision/
├── 01-Domain/
├── 01-Roadmap/
├── 02-Architecture/
├── 03-Learning/
├── 04-DECISIONS/
└── 06-Journal/

tests/
└── domain/application/architecture tests
```

## Architectural Intent

The exact directory layout may evolve.

The important invariant is separation of responsibilities and dependency direction.

Do not reorganize folders merely for aesthetics. Change structure when a boundary or responsibility has a clear reason to change.
