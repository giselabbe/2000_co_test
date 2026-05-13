import sqlite3
import pytest

import co.bdd_voies as bdd
from co.perso_data import Peuple, Famille, Profil
from co.perso_creation import (
    Modificateurs,
    Capacite,
    classe_skill_from_bdd,
)


def test_flatten_peuple_for_basic():
    data = {
        "HUMAIN": {
            "DIVERSITE": {
                "rang": 1,
                "label": "Diversité",
                "description": "Ajoute 1 PC",
                "modif": {"PC": 1},
                "is_magic": 0,
                "action": None,
                "attaque": None,
            }
        }
    }

    rows = bdd.flatten_peuple_for("HUMAIN", data)

    assert isinstance(rows, list)
    assert len(rows) == 1

    row = rows[0]

    assert row["peuple_id"] == "HUMAIN"
    assert row["rang"] == 1
    assert row["label"] == "Diversité"
    assert row["description"] == "Ajoute 1 PC"
    assert row["modif"] == '{"PC": 1}'
    assert row["is_magic"] == 0
    assert row["action"] is None
    assert row["attaque"] is None


def test_get_ppl_capacity_details_found(tmp_path):
    db_path = tmp_path / "test_bdd.sqlite"

    conn = sqlite3.connect(db_path)
    bdd.init_db(conn)
    bdd.upsert_enum_table(conn, "peuples", Peuple)

    rows = [
        {
            "peuple_id": "HUMAIN",
            "rang": 1,
            "label": "Diversité",
            "description": "Ajoute 1 PC",
            "modif": '{"PC": 1}',
            "is_magic": 0,
            "action": None,
            "attaque": None,
        }
    ]
    bdd.upsert_capacite_peuple(conn, rows)
    conn.close()

    label, description, modif, is_magic, action, attaque = (
        bdd.get_ppl_capacity_details(str(db_path), "HUMAIN", 1)
    )

    assert label == "Diversité"
    assert description == "Ajoute 1 PC"
    assert modif == '{"PC": 1}'
    assert is_magic == 0
    assert action is None
    assert attaque is None


def test_classe_skill_from_bdd(tmp_path):
    db_path = tmp_path / "test_bdd.sqlite"

    conn = sqlite3.connect(db_path)
    bdd.init_db(conn)
    bdd.upsert_enum_table(conn, "classes", Profil)

    conn.execute(
        "INSERT INTO voies(id, label, classe_id) VALUES (?, ?, ?)",
        ("VOIE_DU_POURFENDEUR", "Voie du Pourfendeur", "BARBARE"),
    )

    rows = [
        {
            "voie_id": "VOIE_DU_POURFENDEUR",
            "rang": 1,
            "label": "Réflexes Éclair",
            "description": "Ajoute INIT et DEF",
            "modif": '{"INIT": 3, "DEF": 1}',
            "is_magic": 0,
            "action": None,
            "attaque": None,
        }
    ]
    bdd.upsert_capacite_classe(conn, rows)
    conn.close()

    skill = classe_skill_from_bdd(
        str(db_path),
        "VOIE_DU_POURFENDEUR",
        1,
    )

    assert isinstance(skill, Capacite)
    assert skill.ref == "VOIE_DU_POURFENDEUR_1"
    assert skill.label == "Réflexes Éclair"
    assert skill.rang == 1
    assert skill.description == "Ajoute INIT et DEF"

    assert isinstance(skill.modifs, Modificateurs)
    assert len(skill.modifs.liste_mods) == 2

    assert skill.modifs.liste_mods[0].caract == "INIT"
    assert skill.modifs.liste_mods[0].val == 3

    assert skill.modifs.liste_mods[1].caract == "DEF"
    assert skill.modifs.liste_mods[1].val == 1

    assert skill.magie is False
    assert skill.action == ""
    assert skill.attaque == ""


def test_get_ppl_capacity_details_not_found(tmp_path):
    db_path = tmp_path / "test_bdd.sqlite"

    conn = sqlite3.connect(db_path)
    bdd.init_db(conn)
    bdd.upsert_enum_table(conn, "peuples", Peuple)
    conn.close()

    with pytest.raises(ValueError):
        bdd.get_ppl_capacity_details(str(db_path), "HUMAIN", 99)


def test_get_cls_capacity_details_not_found(tmp_path):
    db_path = tmp_path / "test_bdd.sqlite"

    conn = sqlite3.connect(db_path)
    bdd.init_db(conn)
    bdd.upsert_enum_table(conn, "classes", Profil)
    conn.close()

    with pytest.raises(ValueError):
        bdd.get_cls_capacity_details(
            str(db_path),
            "VOIE_DU_POURFENDEUR",
            99,
        )


