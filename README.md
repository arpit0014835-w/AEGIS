<div align="center">

# 🛡️ AEGIS

### AI-Generated Code Trust Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docs.docker.com/compose/)

**Detect AI-generated code · Scan for AI-specific vulnerabilities · Verify cryptographic authorship**

[Quick Start](#-quick-start) · [Architecture](#-architecture) · [API Reference](#-api-reference) · [Dashboard](#-dashboard) · [Supported Languages](#-supported-languages)

</div>

---

## 🎯 The Problem

AI coding assistants are mainstream — over 67% of developers use AI tools (GitHub Octoverse 2024). But AI-generated code introduces invisible risks:

| Risk | Impact |
|------|--------|
| **No Visibility** | Organizations can't measure AI-generated code in repositories |
| **AI-Specific Security** | Hallucinated dependencies, prompt injection, unvalidated AI outputs |
| **Unprovable Authorship** | No cryptographic proof of human authorship for compliance |

## 💡 The Solution

AEGIS provides a **Codebase Trust Score (0–100)** through three integrated analysis pillars:

| Pillar | Weight | What It Does |
|--------|--------|-------------|
| 👻 **Ghost Detect** | 35% | **Hybrid AI detection** — ML model (XGBoost) for Python/.ipynb + multi-signal heuristic analyzer for all other languages + hallucinated dependency detection |
| 🛡️ **Breach Secure** | 40% | AI-aware security scanning (Semgrep + custom rules) + prompt injection detection |
| 🔏 **Proof Verify** | 25% | Cryptographic authorship watermarks (SHA-256 + steganography) |

<div align="center">
<br>

```
Trust Score = (Ghost Detect × 0.35) + (Breach Secure × 0.40) + (Proof Verify × 0.25)
```

</div>

---

## ✨ Features

- **Multi-input support** — Scan via GitHub URL, file upload (50+ extensions), or archive upload (.zip, .rar, .7z, .tar.gz)
- **40+ language support** — Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, Ruby, PHP, Swift, Kotlin, and many more
- **Real-time progress tracking** — Live scan stage updates via polling with resilient error handling
- **Interactive dashboard** — D3.js-powered visualizations with trust gauge, file heatmap, and vulnerability charts
- **Custom Semgrep rules** — AI-specific security rules for hallucinated imports, insecure LLM calls, and prompt injection
- **Hybrid AI detection** — XGBoost ML model for Python/.ipynb files + language-agnostic heuristic analyzer (7 signals) for all other languages
- **Jupyter Notebook support** — Extracts Python code cells from `.ipynb` files and analyzes them with the trained ML model
- **Cryptographic watermarking** — SHA-256 steganographic authorship verification per file
- **Docker-ready** — Full docker-compose setup for one-command deployment
- **REST API** — Interactive Swagger docs at `/docs`

---

## 🤖 Hybrid AI Detection (Ghost Detect)

Ghost Detect uses a **hybrid approach** to maximize detection accuracy across all programming languages:

### Python / Jupyter Notebook Files → ML Model

For `.py` and `.ipynb` files, AEGIS uses a **trained XGBoost classifier** with **38 engineered code features**:

| Feature Category | Count | Examples |
|-----------------|-------|---------|
| **Stylometric** | 8 | Line length stats, blank line ratio, indentation consistency |
| **AST Structural** | 7 | Function depth, nesting level, node type distribution |
| **Token Frequency** | 8 | Keyword ratios, operator density, built-in usage |
| **Cyclomatic Complexity** | 2 | McCabe complexity, branch density |
| **Identifier Naming** | 7 | Avg name length, snake_case ratio, naming entropy |
| **Comment Density** | 3 | Comment ratio, docstring presence, inline commenting |
| **Entropy & Repetition** | 4 | Shannon entropy, token uniqueness, bigram repetition |

For `.ipynb` notebooks, code cells are automatically extracted from the JSON structure before feature extraction.

**Train your own model:**
```bash
cd backend
python train_model.py --human-csv ../human_selected_dataset.csv --ai-csv ../created_dataset_with_llms.csv
```

### All Other Languages → Heuristic Analyzer

For non-Python files (JavaScript, Java, Go, Rust, C++, etc.), AEGIS uses a **7-signal weighted heuristic analyzer**:

| Signal | Weight | What It Detects |
|--------|--------|----------------|
| Comment Pattern | 20% | Section dividers, step-by-step comments, overly descriptive comments |
| Line Length Uniformity | 15% | Unnaturally consistent line lengths (low coefficient of variation) |
| Naming Regularity | 15% | Long descriptive names, consistent conventions, few single-char vars |
| Entropy & Repetition | 15% | Low token uniqueness, high bigram repetition |
| Structural Regularity | 15% | Consistent indentation, regular blank line spacing |
| Boilerplate Ratio | 10% | Try-catch templates, null checks, TODO patterns |
| Docstring Density | 10% | Doc-to-function ratio, type annotation density |

Each signal produces a score (0.0–1.0), and the weighted combination gives the final AI probability.

### Detection Method Tracking

Every file in the report includes a `detection_method` field:
- `ml_model` — Analyzed with the trained XGBoost classifier (Python/.ipynb)
- `heuristic` — Analyzed with the multi-signal heuristic analyzer (all other languages)
- `skipped` — Empty file, no analysis performed

---

## 🚀 Quick Start

### Prerequisites

| Tool | Required | Purpose |
|------|----------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| Git | Latest | Repository cloning |
| Redis | 7+ (optional) | Job queue (falls back to in-memory) |
| Docker | Latest (optional) | Containerized deployment |

### Option 1: Local Development

#### 1. Clone & Configure

```bash
git clone https://github.com/your-org/aegis.git
cd aegis
cp .env.example .env       # Optional — defaults work out of the box
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup

```bash
cd frontend
npm install
```

#### 4. Start Services

```bash
# Terminal 1 — Backend API
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

#### 5. Open Dashboard

Navigate to **http://localhost:3000** and submit a GitHub URL or upload a file!

### Option 2: Docker

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14 + D3.js)                │
│  Trust Gauge │ File Heatmap │ Vuln Chart │ Watermark Status     │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                     Backend API (FastAPI)                        │
│  POST /scans  │  POST /scans/upload  │  GET /scans/{id}        │
│  GET /reports/{id}  │  GET /health                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ Background Tasks
┌────────────────────────────▼────────────────────────────────────┐
│                     Analysis Pipeline                            │
│                                                                  │
│  ┌───────────┐   ┌──────────────┐   ┌───────────────┐          │
│  │ Ingestion │──▶│ Ghost Detect │──▶│ Breach Secure │          │
│  │ Git/Upload│   │ Hybrid ML +  │   │ Semgrep/Rules │          │
│  └───────────┘   │ Heuristics   │   └───────┬───────┘          │
│                   └──────────────┘           │                   │
│                                              │                   │
│                  ┌──────────────┐   ┌────────▼──────┐           │
│                  │ Trust Score  │◀──│ Proof Verify  │           │
│                  │ Weighted Avg │   │ SHA-256/Steg  │           │
│                  └──────┬───────┘   └───────────────┘           │
│                         │                                        │
│                    ┌────▼────┐                                   │
│                    │ Report  │                                   │
│                    └─────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI, Pydantic, uvicorn | Async REST API with validation |
| **ML/AI** | scikit-learn, XGBoost, NumPy | Hybrid AI code detection (ML + heuristics) |
| **Security** | Semgrep, custom YAML rules | Static analysis for AI-specific vulns |
| **Crypto** | cryptography (SHA-256) | Watermark generation & verification |
| **Frontend** | Next.js 14, React 18, D3.js | Interactive dashboard & visualizations |
| **Styling** | Tailwind CSS | Utility-first responsive design |
| **State** | @tanstack/react-query | Server state management & polling |
| **Queue** | Redis (optional) | Job queue with in-memory fallback |
| **Logging** | structlog | Structured JSON logging |
| **Infra** | Docker Compose, Azure Bicep | Container orchestration & IaC |
| **CI/CD** | GitHub Actions | Automated testing & deployment |

---

## 📡 API Reference

Base URL: `http://localhost:8000/api/v1`

### Scan a GitHub Repository

```bash
curl -X POST http://localhost:8000/api/v1/scans \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/expressjs/express"}'
```

**Response:**
```json
{
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued"
}
```

### Upload a File or Archive

Supports `.zip`, `.rar`, `.7z`, `.tar.gz`, `.py`, `.js`, `.ts`, `.java`, `.go`, `.rs`, and 50+ more extensions.

```bash
# Upload a ZIP archive
curl -X POST http://localhost:8000/api/v1/scans/upload \
  -F "file=@codebase.zip"

# Upload a single source file
curl -X POST http://localhost:8000/api/v1/scans/upload \
  -F "file=@main.py"
```

### Poll Scan Status

```bash
curl http://localhost:8000/api/v1/scans/{scan_id}
```

**Response:**
```json
{
  "scan_id": "a1b2c3d4-...",
  "status": "ghost_detect",
  "current_stage": "ghost_detect",
  "progress": 45
}
```

### Get Full Report

```bash
curl http://localhost:8000/api/v1/reports/{scan_id}
```

**Response:**
```json
{
  "scan_id": "a1b2c3d4-...",
  "trust_score": 64.5,
  "ghost_detect": { "score": 72.0, "files_analyzed": 148 },
  "breach_secure": { "score": 58.0, "vulnerabilities": [...] },
  "proof_verify":  { "score": 68.0, "watermarks": [...] }
}
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

> 📖 **Full interactive Swagger docs** available at [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📊 Dashboard

The web dashboard provides real-time scan monitoring and interactive result visualization:

| Component | Description |
|-----------|-------------|
| **Trust Score Gauge** | Animated D3.js radial gauge showing the final score (0–100) with color-coded severity |
| **File Heatmap** | Treemap visualization showing per-file AI generation probability |
| **Vulnerability Chart** | Bar chart breaking down findings by severity (Critical/High/Medium/Low/Info) |
| **Watermark Status** | Per-file cryptographic authorship verification details |
| **Scan Progress** | Live stage-by-stage progress tracking (Queued → Ingesting → Analyzing → Scoring → Complete) |

### Scan Flow

1. **Enter a GitHub URL** or **upload a file/archive** on the landing page
2. Watch real-time progress as AEGIS analyzes the codebase
3. View the interactive trust report with detailed findings

---

## 🌐 Supported Languages

AEGIS supports analysis of **40+ programming languages and file formats**:

| Category | Languages |
|----------|-----------|
| **Web** | JavaScript, TypeScript, HTML, CSS, SCSS, SASS, LESS, Vue, Svelte |
| **Backend** | Python, Jupyter Notebooks (.ipynb), Java, Kotlin, Scala, Groovy, Go, Rust, Ruby, PHP, Perl, Lua, R |
| **Systems** | C, C++, C#, Objective-C |
| **Mobile** | Swift, Dart, Kotlin |
| **Shell** | Bash/Shell, PowerShell, Batch |
| **Config/Data** | JSON, YAML, TOML, XML, INI, SQL |
| **Infrastructure** | Terraform, HCL, Dockerfile |
| **Documentation** | Markdown, reStructuredText |

### Supported Upload Formats

| Type | Extensions |
|------|-----------|
| **Archives** | `.zip`, `.rar`, `.7z`, `.tar`, `.tar.gz`, `.tar.bz2`, `.tar.xz`, `.tgz`, `.gz`, `.bz2`, `.xz` |
| **Source Files** | `.py`, `.ipynb`, `.js`, `.ts`, `.jsx`, `.tsx`, `.java`, `.kt`, `.go`, `.rs`, `.c`, `.cpp`, `.rb`, `.php`, and 40+ more |

---

## 📁 Project Structure

```
aegis/
├── backend/                        # FastAPI backend
│   ├── main.py                     # App factory & CORS setup
│   ├── config.py                   # Pydantic settings
│   ├── api/
│   │   └── v1/                     # REST endpoints
│   │       ├── scans.py            # POST /scans, POST /scans/upload, GET /scans/{id}
│   │       ├── reports.py          # GET /reports/{id}
│   │       └── health.py          # GET /health
│   ├── models/                     # Pydantic schemas & enums
│   │   ├── enums.py               # ScanStatus, Severity, Language, InputType
│   │   ├── scan.py                # Scan request/response models
│   │   └── report.py             # Report response models
│   ├── services/                   # Core analysis pipeline
│   │   ├── ingestion.py           # Git clone, archive extraction, file staging
│   │   ├── ghost_detect.py        # Hybrid AI detection (ML for Python, heuristics for others)
│   │   ├── breach_secure.py       # Security scanning (Semgrep + pattern rules)
│   │   ├── proof_verify.py        # SHA-256 steganographic watermarking
│   │   ├── trust_score.py         # Weighted score aggregation
│   │   └── ml/                    # ML model training & evaluation
│   │       ├── trainer.py         # XGBoost model trainer with Optuna tuning
│   │       ├── feature_extractor.py  # 38 Python code features (AST, stylometric, entropy)
│   │       ├── heuristic_analyzer.py # Language-agnostic 7-signal heuristic detector
│   │       ├── preprocessing.py   # Data preprocessing
│   │       └── evaluate.py        # Model evaluation metrics
│   ├── rules/semgrep/             # Custom AI-specific Semgrep rules
│   │   ├── ai_hallucinated_import.yaml
│   │   ├── insecure_llm_call.yaml
│   │   └── prompt_injection.yaml
│   ├── workers/                    # Background scan worker
│   ├── utils/                      # Helpers (git, file parser, crypto, logger)
│   ├── tests/                      # Pytest test suite
│   └── models/saved/              # Pre-trained ML model artifacts
├── frontend/                       # Next.js 14 dashboard
│   └── src/
│       ├── app/                   # Pages (landing, dashboard/[scanId])
│       ├── components/            # React components with D3.js
│       │   ├── TrustScoreGauge.js
│       │   ├── FileHeatmap.js
│       │   ├── VulnerabilityChart.js
│       │   ├── WatermarkStatus.js
│       │   ├── ScanForm.js
│       │   ├── Navbar.js
│       │   └── Footer.js
│       ├── hooks/                 # Custom hooks (useScanStatus)
│       └── lib/                   # API client (axios)
├── infra/
│   ├── azure/                     # Azure Bicep templates
│   │   ├── container-app.bicep
│   │   └── redis.bicep
│   └── ci/
│       └── github-actions.yml     # CI/CD pipeline
├── docker-compose.yml             # Full-stack Docker setup
└── README.md
```

---

## 🧪 Testing

```bash
# Run backend unit tests
cd backend
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=services --cov=utils --cov-report=term-missing

# Frontend lint check
cd frontend
npm run lint

# Frontend production build
npm run build
```

---

## 🔧 Configuration

AEGIS works out of the box with sensible defaults. All settings can be overridden via environment variables or a `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string (optional — in-memory fallback) | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint for LLM analysis (optional) | — |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key (optional) | — |
| `AZURE_OPENAI_DEPLOYMENT` | Azure OpenAI deployment name (optional) | — |
| `SEMGREP_RULES_DIR` | Custom Semgrep rules directory | `rules/semgrep` |
| `MAX_REPO_SIZE_MB` | Maximum repository size for cloning | `500` |
| `CLONE_DIR` | Temp directory for cloned repos | `tmp/repos` |
| `UPLOAD_DIR` | Temp directory for uploaded files | `tmp/uploads` |

### Optional Enhancements

| Tool | Purpose | Install |
|------|---------|---------|
| Redis | Persistent job queue (instead of in-memory) | `docker run -d -p 6379:6379 redis:7-alpine` |
| Semgrep | Advanced static analysis rules | `pip install semgrep` |
| 7-Zip CLI | Support for .7z archive extraction | [7-zip.org](https://www.7-zip.org/) |
| UnRAR | Support for .rar archive extraction | [rarlab.com](https://www.rarlab.com/) |

---

## 🐳 Docker Deployment

The `docker-compose.yml` starts all services with a single command:

```bash
docker-compose up --build
```

This spins up:

| Service | Container | Port |
|---------|-----------|------|
| Redis | `redis:7-alpine` | 6379 |
| Backend API | `aegis-backend` | 8000 |
| Scan Worker | `aegis-worker` | — |
| Frontend | `aegis-frontend` | 3000 |

For production, create a `.env` file with your Azure OpenAI credentials for enhanced LLM-based vulnerability analysis.

---

## 🛣️ Roadmap

- [ ] GitHub App integration for automated PR scanning
- [ ] VS Code extension for real-time analysis
- [ ] Support for GitLab and Bitbucket repositories
- [ ] Custom ML model training on organization-specific codebases
- [ ] SBOM (Software Bill of Materials) generation
- [ ] Webhook notifications for scan completion
- [ ] Team/organization dashboards with historical trends
- [ ] SARIF export for integration with GitHub Security tab

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please ensure:
- All existing tests pass (`python -m pytest tests/ -v`)
- New features include appropriate tests
- Code follows the existing style (Ruff for Python, ESLint for JavaScript)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for a trustworthy AI-augmented future.**

[⬆ Back to Top](#-aegis)

</div>
