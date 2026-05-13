import sqlite3
import json
from typing import Dict, List
from co.perso_data import Peuple, Famille, Profil
from co.io_helpers import load_yaml


def init_db(conn: sqlite3.Connection):
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def upsert_enum_table(conn: sqlite3.Connection, table: str, enum_cls):
    """
    Insère/Met à jour une table de référentiel à partir d'un Enum :
    - id = enum.name (ex: ELFE_HAUT)
    - label = enum.value (ex: "Elfe Haut")
    """
    sql = f"INSERT INTO {table}(id, label) VALUES(?, ?) ON CONFLICT(id) DO UPDATE SET label=excluded.label"
    rows = [(e.name, e.value) for e in enum_cls]
    conn.executemany(sql, rows)
    conn.commit()


def format_voie_label(voie_id: str) -> str:
    """
    Génère un label lisible à partir de l'ID (fallback).
    Ex: 'VOIE_DE_L_AIR' -> 'Voie De L Air'
    Astuce: tu peux remplacer par un mapping manuel si tu veux 'Voie de l'Air'.
    """
    return voie_id.replace("_", " ").title()


def upsert_voies_from_yaml(conn: sqlite3.Connection, data: dict):
    """
    Pour chaque classe, upsert toutes les voies (clés sous la classe).
    """
    sql = (
        "INSERT INTO voies(id, label, classe_id) VALUES(?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET label=excluded.label, classe_id=excluded.classe_id"
    )
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


def flatten_capacite_classe_for(
    classe_id: str, voie_id: str, data: Dict
) -> List[Dict]:
    """
    Extrait une liste d'objets 'capacite_classe' normalisés à partir du YAML :
    {
      "voie_id": str, "rang": int, "label": str,
      "description": str|None, "modif": json|None, "is_magic": int, "action": str|None, "attaque": json|None
    }
    """
    if classe_id not in data:
        raise ValueError(f"Classe '{classe_id}' absente du YAML.")
    cls_node = data[classe_id]
    if voie_id not in cls_node:
        raise ValueError(
            f"Voie '{voie_id}' absente sous la classe '{classe_id}'."
        )

    out: List[Dict] = []
    for key, props in cls_node[voie_id].items():
        if "label" not in props or "rang" not in props:
            raise ValueError(
                f"Entrée '{key}' incomplète: 'label' et 'rang' requis."
            )
        rang = int(props["rang"])
        if not (1 <= rang <= 5):
            raise ValueError(
                f"Rang invalide {rang} pour '{key}' (doit être 1..5)."
            )

        modif_json = (
            json.dumps(props.get("modif", {}), ensure_ascii=False)
            if props.get("modif")
            else None
        )
        attaque_json = (
            json.dumps(props.get("attaque", {}), ensure_ascii=False)
            if props.get("attaque")
            else None
        )

        out.append(
            {
                "voie_id": voie_id,
                "rang": rang,
                "label": props["label"],
                "description": props.get("description"),
                "modif": modif_json,
                "is_magic": int(props.get("is_magic", 0)),
                "action": props.get("action"),
                "attaque": attaque_json,
            }
        )

    out.sort(key=lambda d: d["rang"])
    return out


def flatten_peuple_for(
    peuple_id: str, dict_capacites: Dict
) -> List[Dict]:
    """
    Extrait une liste d'objets 'capacites' normalisés à partir du YAML brut:
    {
      "peuple_id": str, "rang": int, "label": str,
      "description": str|None, "modif": json|None, "is_magic": int, "action": str|None, "attaque": json|None
    }
    """
    out = []
    for key, props in dict_capacites[peuple_id].items():
        rang = int(props["rang"])
        modif_json = (
            json.dumps(props.get("modif", {}), ensure_ascii=False)
            if props.get("modif")
            else None
        )
        attaque_json = (
            json.dumps(props.get("attaque", {}), ensure_ascii=False)
            if props.get("attaque")
            else None
        )

        out.append(
            {
                "peuple_id": peuple_id,
                "rang": rang,
                "label": props["label"],
                "description": props.get("description"),
                "modif": modif_json,
                "is_magic": int(props.get("is_magic", 0)),
                "action": props.get("action"),
                "attaque": attaque_json,
            }
        )

    out.sort(key=lambda d: d["rang"])
    return out


def upsert_capacite_classe(conn: sqlite3.Connection, rows: List[Dict]):
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


def upsert_capacite_peuple(conn, rows):
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
    conn: sqlite3.Connection, data: Dict
):
    """
    Parcourt TOUTES les classes et TOUTES les voies du YAML et upsert leurs capacite_classe.
    """
    for classe_id, voies in data.items():
        if not isinstance(voies, dict):
            continue
        for voie_id, capacite_classe_map in voies.items():
            rows = flatten_capacite_classe_for(classe_id, voie_id, data)
            upsert_capacite_classe(conn, rows)


def upsert_all_capacites_peuple_from_yaml(conn, dict_capacites):
    """
    Parcourt ls capacités de peuple et les insère.
    """
    for peuple_id in dict_capacites.keys():
        rows = flatten_peuple_for(peuple_id, dict_capacites)
        upsert_capacite_peuple(conn, rows)


def get_cls_capacity_details(bdd_path, voie_id, rang):
    sql = f"""
    SELECT label, description, modif, is_magic, action, attaque 
    FROM capacite_classe 
    WHERE voie_id = '{voie_id}' AND rang = {rang};
    """
    conn = sqlite3.connect(bdd_path)
    cursor = conn.cursor()
    cursor.execute(sql)
    label, description, modif, is_magic, action, attaque = (
        cursor.fetchone()
    )

    return (label, description, modif, is_magic, action, attaque)


def get_ppl_capacity_details(bdd_path, peuple_id, voie_rang):
    sql = f"""
    SELECT label, description, modif, is_magic, action, attaque 
    FROM capacite_peuple 
    WHERE peuple_id = '{peuple_id}' AND rang = {voie_rang};
    """
    conn = sqlite3.connect(bdd_path)
    cursor = conn.cursor()
    cursor.execute(sql)
    label, description, modif, is_magic, action, attaque = (
        cursor.fetchone()
    )

    return (label, description, modif, is_magic, action, attaque)


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
)
;
"""

CAPACITE_CLASSE_SQL = """
INSERT INTO capacite_classe (voie_id, rang, label, description, modif, is_magic, action, attaque)
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
INSERT INTO  capacite_peuple (peuple_id, rang, label, description, modif, is_magic, action, attaque)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(peuple_id, rang) DO UPDATE SET
  label       = excluded.label,
  description = excluded.description,
  modif       = excluded.modif,
  is_magic    = excluded.is_magic,
  action      = excluded.action,
  attaque     = excluded.attaque;
"""

# 1) Crée la strusture et les Peuples / Classes
DB_PATH = "data/database_test.db"


def initiate_full_database(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    upsert_enum_table(conn, "peuples", Peuple)
    upsert_enum_table(conn, "familles", Famille)
    upsert_enum_table(conn, "classes", Profil)

    # 2) Charger les Voies
    file_voies_classes = "data/lst_voies.yml"
    voies_classes = load_yaml(file_voies_classes)
    upsert_voies_from_yaml(conn, voies_classes)
    upsert_all_capacite_classe_from_yaml(conn, voies_classes)

    file_voies_peuples = "data/lst_voies_peuples.yml"
    voies_peuples = load_yaml(file_voies_peuples)
    upsert_all_capacites_peuple_from_yaml(conn, voies_peuples)
    conn.close()


# initiate_full_database(DB_PATH)
