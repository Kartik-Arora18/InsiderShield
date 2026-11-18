# \# InsiderShield

# 

# \*\*An ML-powered Insider Threat Detection and Investigation Platform\*\*

# 

# InsiderShield is a full-stack security analytics platform that detects potentially risky employee activity, identifies anomalous behaviour, and supports security investigations through explainable alerts and audit history.

# 

# \## Key Features

# 

# \- Event ingestion and validation

# \- Employee-specific anomaly detection using Isolation Forest

# \- Rule-based detection for suspicious activity

# \- Risk scoring using anomaly, severity, frequency, and recency

# \- Explainable security alerts

# \- Investigation management and audit history

# \- JWT authentication, role-based access control (RBAC), and tenant isolation

# \- Asynchronous background processing using Celery

# 

# \## Tech Stack

# 

# | Layer | Technologies |

# |---|---|

# | Backend | Python, FastAPI, SQLAlchemy |

# | Frontend | React, TypeScript, Vite |

# | Database | PostgreSQL |

# | Background processing | Redis, Celery |

# | Machine Learning | Scikit-learn, Isolation Forest |

# | Migrations | Alembic |

# | Infrastructure | Docker, Docker Compose |

# | Testing | Pytest |

# 

# \## Architecture

# 

# ```text

# React + TypeScript Frontend

# &#x20;         |

# &#x20;         v

# &#x20;    FastAPI Backend

# &#x20;         |

# &#x20;   +-----+------+

# &#x20;   |            |

# &#x20;   v            v

# PostgreSQL    Redis

# &#x20;                |

# &#x20;                v

# &#x20;            Celery Worker

# &#x20;                |

# &#x20;                v

# &#x20;       Anomaly Detection

# &#x20;       and Risk Scoring

# ```

# 

# \## Run Locally

# 

# \### Prerequisites

# 

# \- Docker Desktop

# \- Docker Compose v2

# 

# \### Setup

# 

# ```powershell

# cd InsiderShield

# 

# Copy-Item .env.example .env

# ```

# 

# Configure the environment variables in `.env` before starting the application.

# 

# \### Start the application

# 

# ```powershell

# docker compose up --build -d

# ```

# 

# \### Run database migrations

# 

# ```powershell

# docker compose exec api alembic upgrade head

# ```

# 

# \### Run backend tests

# 

# ```powershell

# docker compose exec api pytest -v

# ```

# 

# \## Machine Learning Approach

# 

# InsiderShield uses employee-specific Isolation Forest models to identify unusual activity based on behavioural features.

# 

# The detection pipeline combines:

# 

# \- Behavioural feature engineering

# \- Historical employee activity baselines

# \- Isolation Forest anomaly detection

# \- Rule-based detection thresholds

# \- Risk scoring and explainable alerts

# 

# \*\*Note:\*\* The current risk score is a heuristic score, not a calibrated probability. Formal model evaluation and benchmarking are planned separately.

# 

# \## Project Structure

# 

# ```text

# InsiderShield/

# ├── backend/

# │   ├── alembic/

# │   ├── app/

# │   │   ├── api/

# │   │   ├── core/

# │   │   ├── db/

# │   │   ├── models/

# │   │   ├── schemas/

# │   │   ├── services/

# │   │   └── worker/

# │   ├── tests/

# │   ├── Dockerfile

# │   └── requirements.txt

# ├── frontend/

# │   ├── src/

# │   │   ├── pages/

# │   │   └── lib/

# │   └── package.json

# ├── docker-compose.yml

# └── .env.example

# ```

# 

# \## Testing

# 

# The backend test suite and frontend production build have been successfully run during development.

# 

# \## Future Improvements

# 

# \- Benchmark anomaly detection using a labelled dataset such as the CMU CERT Insider Threat dataset

# \- Add precision, recall, F1-score and false-positive analysis

# \- Improve model evaluation and threshold tuning

# \- Add richer monitoring and operational metrics

# 

# \## Author

# 

# \*\*Kartik Arora\*\*

# 

# B.Tech Computer Science and Engineering

# 

# \[GitHub](https://github.com/Kartik-Arora18)



