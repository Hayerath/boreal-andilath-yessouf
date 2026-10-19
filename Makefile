PY ?= python3
.PHONY: install load test reload docs dashboard all
install:   ; $(PY) -m pip install -r requirements.txt
load:      ; $(PY) -m src.pipeline run                    # ingestion + qualité + cœur + marts + tests bloquants
test:      ; $(PY) -m pytest -q tests                     # rejeu, double livraison, rechargement, test bloquant
reload:    ; $(PY) -m src.pipeline reload --month $(MONTH) # ex. make reload MONTH=2024_03
docs:      ; $(PY) -m src.gen_docs                        # régénère docs/regles_qualite.md depuis l'entrepôt
dashboard: ; $(PY) -m streamlit run app/dashboard.py   # livrable 5
all: install load test docs
