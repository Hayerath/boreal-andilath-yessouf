"""Lancement planifie du pipeline, avec journal et alerte en cas d'echec.

  python scripts/orchestrate.py            # a lancer chaque jour/mois par le planificateur
  python scripts/orchestrate.py --reload 2024_03

- Sans nouveau fichier, le pipeline ne recharge rien (empreinte inchangee) : le lancer souvent est sans risque.
- Un echec (fichier illisible, schema modifie, test bloquant) donne un code de sortie non nul : on ecrit
  logs/ALERTE.txt et, si la variable BOREAL_ALERT_WEBHOOK est definie, on envoie le message a cette adresse.
- Le coeur reste dans son dernier etat valide (les transformations sont annulees).
"""
import argparse, json, os, subprocess, sys, urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"


def alert(message: str):
    LOGS.mkdir(exist_ok=True)
    (LOGS / "ALERTE.txt").write_text(message, encoding="utf-8")
    url = os.environ.get("BOREAL_ALERT_WEBHOOK")
    if url:
        try:
            req = urllib.request.Request(url, data=json.dumps({"text": message}).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:  # l'alerte ne doit jamais masquer l'echec d'origine
            print("envoi de l'alerte impossible :", e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reload", help="mois a recharger, ex. 2024_03")
    p.add_argument("--src", help="dossier des sources (par defaut data/sources)")
    a = p.parse_args()
    cmd = [sys.executable, "-m", "src.pipeline"] + (["reload", "--month", a.reload] if a.reload else ["run"])
    if a.src:
        cmd += ["--src", a.src]
    LOGS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = LOGS / f"pipeline_{stamp}.log"
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}  # sortie du pipeline en UTF-8 quelle que soit la console Windows
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    log.write_text((r.stdout or "") + (r.stderr or ""), encoding="utf-8")
    print((r.stdout or "").strip())
    if r.returncode != 0:
        msg = f"Boreal : echec du pipeline le {stamp}. Coeur inchange. Voir {log.name}.\n" + (r.stderr or "")[-1500:]
        alert(msg)
        print("ALERTE :", msg.splitlines()[0])
        sys.exit(r.returncode)
    ok = LOGS / "ALERTE.txt"
    if ok.exists():
        ok.unlink()  # l'alerte disparait quand un passage reussit


if __name__ == "__main__":
    main()
