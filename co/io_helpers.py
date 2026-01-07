import json, yaml
from typing import Any, Dict, List, Tuple

# Fonctions de Sérialisations JSON et YAML


def save_json(
    data: Dict[str, Any], path: str, *, indent: int = 2, ensure_ascii: bool = False
) -> None:
    """
    Enregistre un dict en JSON dans un fichier.
    - indent=2 : JSON lisible
    - ensure_ascii=False : conserve les accents (utf-8)
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)


def load_json(path: str) -> Dict[str, Any]:
    """Charge un dict depuis un fichier JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_yaml(data: Dict[str, Any], path: str) -> None:
    """
    Enregistre un dict en YAML (YML) dans un fichier.
    Nécessite PyYAML (pip install PyYAML).
    """

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            allow_unicode=True,  # conserve les accents
            sort_keys=False,  # respecte l'ordre des clés si dict ordonné
        )


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
