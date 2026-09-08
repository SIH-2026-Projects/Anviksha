# God'sEye

Server-side scientific backend for SIH26067.

## Responsibility

This service owns:

- CF-aware model data access
- server-side spatial/depth/time subsetting
- scientific interpolation
- model-observation collocation
- model-observation comparison
- confidence/comparability metadata
- ocean diagnostics
- REST API contracts

It does **not** own browser rendering, GPU/WebGL code, or large-scale data engineering such as chunking/LOD pipelines. Those remain separate team responsibilities.

## Architecture

```text
NetCDF / observation sources
          |
          v
   Data access layer
          |
          v
 Server-side subsetting
          |
          v
 Scientific engine
  |       |       |
  v       v       v
collocation comparison diagnostics
  \       |       /
       evidence
          |
          v
      FastAPI REST
          |
          v
       Frontend
```

## Important rule

The scientific engine must not depend on FastAPI. The same functions used by the API must be testable directly with Python objects. This prevents the API layer from becoming coupled to the mathematics and makes later serving changes safe.

## Setup with uv

```bash
uv sync --extra dev
uv run pytest
uv run uvicorn ocean_backend.api.main:app --reload
```

The optional large-data serving and database dependencies are intentionally not installed yet:

```bash
uv sync --extra dev --extra data --extra serving --extra database
```

Only add those extras when their corresponding integration is implemented.
