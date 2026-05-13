import sqlite3
import json
from typing import Any, Dict, List, Tuple, Optional

from co.perso_data import Peuple, Famille, Profil
from co.io_helpers import load_yaml

# =========================
# Helpers internes
# =========================


def _connect(db_path: str) -> sqlite3.Connection:
    """
    Ouvre une connexion SQLite avec les clés étrangères activées.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _json_or_none(value: Any) -> Optional[str]:
    """
    Sérialise en JSON si la valeur est non vide, sinon None.
    """
    if value in (None, {}, []):
        return None
    return json.dumps(value, ensure_ascii=False)


def _loads_json_or_empty_dict(value: Optional[str]) -> Dict[str, Any]:
    """
    Désérialise une chaîne JSON vers un dict.
    Retourne {} si la valeur est None ou vide.
    """
    if not value:
        return {}
    return json.loads(value)


def _validate_capacity_props(props: Dict[str, Any], key: str) -> int:
    """
    Valide les champs minimaux d'une capacité et retourne le rang.
    """
    if "label" not in props or "rang" not in props:
        raise ValueError(
            f"Entrée '{key}' incomplète : 'label' et 'rang' requis."
        )

    rang = int(props["rang"])
    if not (1 <= rang <= 5):
        raise ValueError(
            f"Rang invalide {rang} pour '{key}' (doit être 1..5)."
        )

    return rang


def _normalize_capacity_row(
    owner_key_name: str,
    owner_id: str,
    props: Dict[str, Any],
    key: str,
) -> Dict[str, Any]:
    """
    Normalise une entrée de capacité issue du YAML.

    Retourne un dict prêt à être inséré dans la BDD :
    {
        owner_key_name: str,   # ex "voie_id" ou "peuple_id"
        "rang": int,
        "label": str,
        "description": str|None,
        "modif": str|None,     # JSON
        "is_magic": int,
        "action": str|None,
        "attaque": str|None,
    }
    """
    rang = _validate_capacity_props(props, key)

    return {
        owner_key_name: owner_id,
        "rang": rang,
        "label": props["label"],
        "description": props.get("description"),
        "modif": _json_or_none(props.get("modif")),
        "is_magic": int(props.get("is_magic", 0)),
        "action": props.get("action"),
        # Ici on suppose que 'attaque' est un champ texte simple
        # (ex: "FOR", "AGI", etc.). Si tu veux un objet JSON plus tard,
        # il faudra harmoniser partout.
        "attaque": props.get("attaque"),
    }


def _fetch_capacity_row(
    bdd_path: str,
    table: str,
    id_field: str,
    id_value: str,
    rang: int,
) -> Tuple[
    str, Optional[str], Optional[str], int, Optional[str], Optional[str]
]:
    """
    Lit une ligne de capacité dans une table donnée.

    Retourne :
    (label, description, modif, is_magic, action, attaque)

    Lève ValueError si aucune ligne n'est trouvée.
    """
    sql = f"""
    SELECT label, description, modif, is_magic, action, attaque
    FROM {table}
    WHERE {id_field} = ? AND rang = ?;
    """

    with _connect(bdd_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (id_value, rang))
        row = cursor.fetchone()

    if row is None:
        raise ValueError(
            f"Aucune capacité trouvée dans {table} "
            f"pour {id_field}={id_value!r}, rang={rang!r}"
        )

    return row


# =========================
# Initialisation / schéma
# =========================

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS peuples (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS familles (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classes (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS voies (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  classe_id TEXT NOT NULL,
  FOREIGN KEY (classe_id) REFERENCES classes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS capacite_classe (
  voie_id      TEXT NOT NULL,
  rang         INTEGER NOT NULL CHECK (rang BETWEEN 1 AND 5),
  label        TEXT NOT NULL,
  description  TEXT,
  modif        TEXT,
  is_magic     INTEGER NOT NULL DEFAULT 0,
  action       TEXT,
  attaque      TEXT,
  PRIMARY KEY (voie_id, rang),
  FOREIGN KEY (voie_id) REFERENCES voies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS capacite_peuple (
  peuple_id    TEXT NOT NULL,
  rang         INTEGER NOT NULL CHECK (rang BETWEEN 1 AND 5),
  label        TEXT NOT NULL,
  description  TEXT,
  modif        TEXT,
  is_magic     INTEGER NOT NULL DEFAULT 0,
  action       TEXT,
  attaque      TEXT,
  PRIMARY KEY (peuple_id, rang),
  FOREIGN KEY (peuple_id) REFERENCES peuples(id) ON DELETE CASCADE
);
"""


CAPACITE_CLASSE_SQL = """
INSERT INTO capacite_classe
    (voie_id, rang, label, description, modif, is_magic, action, attaque)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(voie_id, rang) DO UPDATE SET
  label       = excluded.label,
  description = excluded.description,
  modif       = excluded.modif,
  is_magic    = excluded.is_magic,
  action      = excluded.action,
  attaque     = excluded.attaque;
"""


CAPACITE_PEUPLE_SQL = """
INSERT INTO capacite_peuple
    (peuple_id, rang, label, description, modif, is_magic, action, attaque)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(peuple_id, rang) DO UPDATE SET
  label       = excluded.label,
  description = excluded.description,
  modif       = excluded.modif,
  is_magic    = excluded.is_magic,
  action      = excluded.action,
  attaque     = excluded.attaque;
"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


# =========================
# Référentiels
# =========================


def upsert_enum_table(
    conn: sqlite3.Connection, table: str, enum_cls
) -> None:
    """
    Insère / met à jour une table de référentiel à partir d'un Enum.

    - id    = enum.name   (ex: HUMAIN)
    - label = enum.value  (ex: "Humain")
    """
    sql = f"""
    INSERT INTO {table}(id, label)
    VALUES(?, ?)
    ON CONFLICT(id) DO UPDATE SET label = excluded.label
    """
    rows = [(e.name, e.value) for e in enum_cls]
    conn.executemany(sql, rows)
    conn.commit()


def format_voie_label(voie_id: str) -> str:
    """
    Génère un label lisible à partir d'un ID technique.
    Ex: 'VOIE_DE_L_AIR' -> 'Voie De L Air'
    """
    return voie_id.replace("_", " ").title()


def upsert_voies_from_yaml(
    conn: sqlite3.Connection, data: Dict[str, Any]
) -> None:
    """
    Pour chaque classe, insère / met à jour toutes les voies.
    """
    sql = """
    INSERT INTO voies(id, label, classe_id)
    VALUES(?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      label = excluded.label,
      classe_id = excluded.classe_id
    """

    rows = []
    for cls_id, voies_node in data.items():
        if not isinstance(voies_node, dict):
            continue

        for voie_id in voies_node.keys():
            label = format_voie_label(voie_id)
            rows.append((voie_id, label, cls_id))

    if rows:
        conn.executemany(sql, rows)
        conn.commit()


# =========================
# Flatten YAML -> rows
# =========================


def flatten_capacite_classe_for(
    classe_id: str,
    voie_id: str,
    data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Extrait une liste d'objets 'capacite_classe' normalisés à partir du YAML.
    """
    if classe_id not in data:
        raise ValueError(f"Classe '{classe_id}' absente du YAML.")

    cls_node = data[classe_id]
    if voie_id not in cls_node:
        raise ValueError(
            f"Voie '{voie_id}' absente sous la classe '{classe_id}'."
        )

    out: List[Dict[str, Any]] = []

    for key, props in cls_node[voie_id].items():
        row = _normalize_capacity_row(
            owner_key_name="voie_id",
            owner_id=voie_id,
            props=props,
            key=key,
        )
        out.append(row)

    out.sort(key=lambda d: d["rang"])
    return out


def flatten_peuple_for(
    peuple_id: str,
    dict_capacites: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Extrait une liste d'objets 'capacite_peuple' normalisés à partir du YAML.
    """
    if peuple_id not in dict_capacites:
        raise ValueError(f"Peuple '{peuple_id}' absent du YAML.")

    out: List[Dict[str, Any]] = []

    for key, props in dict_capacites[peuple_id].items():
        row = _normalize_capacity_row(
            owner_key_name="peuple_id",
            owner_id=peuple_id,
            props=props,
            key=key,
        )
        out.append(row)

    out.sort(key=lambda d: d["rang"])
    return out


# =========================
# Upserts capacités
# =========================


def upsert_capacite_classe(
    conn: sqlite3.Connection, rows: List[Dict[str, Any]]
) -> None:
    params = [
        (
            r["voie_id"],
            r["rang"],
            r["label"],
            r["description"],
            r["modif"],
            r["is_magic"],
            r["action"],
            r["attaque"],
        )
        for r in rows
    ]
    conn.executemany(CAPACITE_CLASSE_SQL, params)
    conn.commit()


def upsert_capacite_peuple(
    conn: sqlite3.Connection, rows: List[Dict[str, Any]]
) -> None:
    params = [
        (
            r["peuple_id"],
            r["rang"],
            r["label"],
            r["description"],
            r["modif"],
            r["is_magic"],
            r["action"],
            r["attaque"],
        )
        for r in rows
    ]
    conn.executemany(CAPACITE_PEUPLE_SQL, params)
    conn.commit()


def upsert_all_capacite_classe_from_yaml(
    conn: sqlite3.Connection,
    data: Dict[str, Any],
) -> None:
    """
    Parcourt toutes les classes et toutes les voies du YAML
    et upsert leurs capacités de classe.
    """
    for classe_id, voies in data.items():
        if not isinstance(voies, dict):
            continue

        for voie_id in voies.keys():
            rows = flatten_capacite_classe_for(classe_id, voie_id, data)
            upsert_capacite_classe(conn, rows)


def upsert_all_capacites_peuple_from_yaml(
    conn: sqlite3.Connection,
    dict_capacites: Dict[str, Any],
) -> None:
    """
    Parcourt toutes les capacités de peuple du YAML et les insère / met à jour.
    """
    for peuple_id in dict_capacites.keys():
        rows = flatten_peuple_for(peuple_id, dict_capacites)
        upsert_capacite_peuple(conn, rows)


# =========================
# Lectures BDD
# =========================


def get_cls_capacity_details(
    bdd_path: str,
    voie_id: str,
    rang: int,
) -> Tuple[
    str, Optional[str], Optional[str], int, Optional[str], Optional[str]
]:
    """
    Retourne :
    (label, description, modif, is_magic, action, attaque)
    """
    return _fetch_capacity_row(
        bdd_path=bdd_path,
        table="capacite_classe",
        id_field="voie_id",
        id_value=voie_id,
        rang=rang,
    )


def get_ppl_capacity_details(
    bdd_path: str,
    peuple_id: str,
    voie_rang: int,
) -> Tuple[
    str, Optional[str], Optional[str], int, Optional[str], Optional[str]
]:
    """
    Retourne :
    (label, description, modif, is_magic, action, attaque)
    """
    return _fetch_capacity_row(
        bdd_path=bdd_path,
        table="capacite_peuple",
        id_field="peuple_id",
        id_value=peuple_id,
        rang=voie_rang,
    )


# =========================
# Initialisation complète
# =========================

DB_PATH = "data/database_test.db"


def initiate_full_database(db_path: str = DB_PATH) -> None:
    """
    Crée la BDD complète à partir des Enums et des fichiers YAML.
    """
    with _connect(db_path) as conn:
        init_db(conn)

        # Référentiels
        upsert_enum_table(conn, "peuples", Peuple)
        upsert_enum_table(conn, "familles", Famille)
        upsert_enum_table(conn, "classes", Profil)

        # Voies + capacités de classe
        file_voies_classes = "data/lst_voies.yml"
        voies_classes = load_yaml(file_voies_classes)
        upsert_voies_from_yaml(conn, voies_classes)
        upsert_all_capacite_classe_from_yaml(conn, voies_classes)

        # Capacités de peuple
        file_voies_peuples = "data/lst_voies_peuples.yml"
        voies_peuples = load_yaml(file_voies_peuples)
        upsert_all_capacites_peuple_from_yaml(conn, voies_peuples)
