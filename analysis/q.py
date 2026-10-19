"""Exécute un fichier .sql (requêtes séparées par ;) sur l'entrepôt et affiche les résultats.
Usage : python analysis/q.py analysis/etape2.sql"""
import sys, duckdb
con = duckdb.connect("data/boreal.duckdb", read_only=True)
for stmt in open(sys.argv[1], encoding="utf-8").read().split(";"):
    if stmt.strip():
        print(con.sql(stmt).df().to_string(index=False), "\n")
