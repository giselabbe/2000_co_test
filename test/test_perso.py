import pytest
from co.perso_creation import (
    Carac,
    Ressource,
    Arme,
    Armure,
    Modificateur,
    Modificateurs,
    Capacite,
    Personnage,
    Capacites,
    Equipement,
)

from co.perso_data import Peuple, Famille, Profil

# PREPARATION #
from dataclasses import dataclass


@dataclass
class FakeCarac:
    AGI: int = 0
    CONST: int = 0
    PER: int = 0
    VOL: int = 0
    CHAR: int = 0


@dataclass
class FakePersonnage:
    peuple: Peuple
    famille: Famille
    niveau: int
    caract: Carac


@pytest.fixture
def make_personnage():
    def _make_personnage(
        peuple=Peuple.HUMAIN,
        famille=Famille.AVENTURIER,
        niveau=1,
        AGI=0,
        CONST=0,
        PER=0,
        CHAR=0,
        VOL=0,
    ):
        return FakePersonnage(
            peuple=peuple,
            famille=famille,
            niveau=niveau,
            caract=Carac(
                AGI=AGI,
                CONST=CONST,
                PER=PER,
                CHAR=CHAR,
                VOL=VOL,
            ),
        )

    return _make_personnage


# TEST CLASSE CARACT #


def test_carac_default_values():
    assert Carac() == Carac(0, 0, 0, 0, 0, 0, 0)


def test_carac_to_dict_returns_dict():
    assert isinstance(Carac().to_dict(), dict)


def test_carac_to_dict_values():
    c = Carac(1, 2, 3, 4, 5, 6, 7)
    assert c.to_dict()["AGI"] == 1


def test_carac_from_dict_values():
    d = {
        "AGI": 1,
        "CONST": 2,
        "FOR": 3,
        "PER": 1,
        "CHAR": 2,
        "INT": 3,
        "VOL": 1,
    }
    c = Carac.from_dict(d)
    assert c.AGI == 1
    assert c.CONST == 2
    assert c.FOR == 3
    assert c.PER == 1
    assert c.CHAR == 2
    assert c.INT == 3
    assert c.VOL == 1


def test_carac_from_dict_missing_keys():
    d = {"AGI": 2}
    c = Carac.from_dict(d)
    assert c.AGI == 2
    assert c.FOR == 0


# TESTS CLASSE RESSOURCE #


def test_ressource_to_dict():
    r = Ressource(
        PV=12,
        DR=(2, 6),
        PM=3,
        PC=4,
        INIT=11,
        DEF=13,
        ATK=5,
        ATD=6,
        ATM=7,
    )

    d = r.to_dict()

    assert isinstance(d, dict)
    assert d["PV"] == 12
    assert d["DR"] == (2, 6)
    assert d["PM"] == 3
    assert d["PC"] == 4
    assert d["INIT"] == 11
    assert d["DEF"] == 13
    assert d["ATK"] == 5
    assert d["ATD"] == 6
    assert d["ATM"] == 7


def test_ressource_from_dict():
    d = {
        "PV": 12,
        "DR": (2, 6),
        "PM": 3,
        "PC": 4,
        "INIT": 11,
        "DEF": 13,
        "ATK": 5,
        "ATD": 6,
        "ATM": 7,
    }

    r = Ressource.from_dict(d)

    assert isinstance(r, Ressource)
    assert r.PV == 12
    assert r.DR == (2, 6)
    assert r.PM == 3
    assert r.PC == 4
    assert r.INIT == 11
    assert r.DEF == 13
    assert r.ATK == 5
    assert r.ATD == 6
    assert r.ATM == 7


def test_bonus_pc_humain_aventurier(make_personnage):
    p = make_personnage(
        peuple=Peuple.HUMAIN,
        famille=Famille.AVENTURIER,
        CHAR=2,
    )
    r = Ressource.from_personnage(p)
    assert r.PC == 6


def test_dr_mystique(make_personnage):
    p = make_personnage(
        famille=Famille.MYSTIQUE,
        CONST=1,
    )
    r = Ressource.from_personnage(p)

    assert r.DR[0] == 4


def test_ressource_from_dict_dr_list_to_tuple():
    d = {
        "PV": 12,
        "DR": [4, 10],
        "PM": 1,
        "PC": 2,
        "INIT": 11,
        "DEF": 11,
        "ATK": 3,
        "ATD": 2,
        "ATM": 2,
    }

    r = Ressource.from_dict(d)

    assert isinstance(r.DR, tuple)
    assert r.DR == (4, 10)


# TEST ARMES, ARMURES #


def test_arme_default_values():

    a = Arme()

    assert a.ref == "ARME"
    assert a.label == "description ARME"
    assert a.DM == "1d6"
    assert a.type_attaque == ""
    assert a.type_degat == ""
    assert a.prix == 0
    assert a.portee == 0
    assert a.obs == ""


def test_arme_to_dict():
    a = Arme(
        ref="EPEE_LONGUE",
        label="Épée longue",
        DM="1d8",
        type_attaque="contact",
        type_degat="tranchant",
        prix=15,
        portee=0,
        obs="arme polyvalente",
    )

    d = a.to_dict()

    assert isinstance(d, dict)
    assert d["ref"] == "EPEE_LONGUE"
    assert d["label"] == "Épée longue"
    assert d["DM"] == "1d8"
    assert d["type_attaque"] == "contact"
    assert d["type_degat"] == "tranchant"
    assert d["prix"] == 15
    assert d["portee"] == 0
    assert d["obs"] == "arme polyvalente"


def test_arme_from_dict_complete():
    d = {
        "ref": "ARC_COURT",
        "label": "Arc court",
        "DM": "1d6",
        "type_attaque": "distance",
        "type_degat": "perforant",
        "prix": 10,
        "portee": 30,
        "obs": "arme simple",
    }

    a = Arme.from_dict(d)

    assert a.ref == "ARC_COURT"
    assert a.label == "Arc court"
    assert a.DM == "1d6"
    assert a.type_attaque == "distance"
    assert a.type_degat == "perforant"
    assert a.prix == 10
    assert a.portee == 30
    assert a.obs == "arme simple"


def test_arme_from_dict_missing_values():
    d = {
        "ref": "DAGUE",
        "label": "Dague",
    }

    a = Arme.from_dict(d)

    assert a.ref == "DAGUE"
    assert a.label == "Dague"
    assert a.DM == "1d6"
    assert a.type_attaque == ""
    assert a.type_degat == ""
    assert a.prix == 0
    assert a.portee == 0
    assert a.obs == ""


# TESTS ARMURES #
def test_armure_default_values():

    a = Armure()

    assert a.ref == "ARMURE"
    assert a.label == "Description d'Armure"
    assert a.prix == 0
    assert isinstance(a.modif, Modificateur)
    assert a.modif.caract == "DEF"
    assert a.modif.val == 0
    assert a.modif.source == ""
    assert a.obs == ""


def test_armure_to_dict():
    a = Armure(
        ref="CUIR",
        label="Armure de cuir",
        prix=50,
        modif=Modificateur(
            caract="DEF", val=2, source="Armure de cuir"
        ),
        obs="légère",
    )

    d = a.to_dict()

    assert isinstance(d, dict)

    assert d["ref"] == "CUIR"
    assert d["label"] == "Armure de cuir"
    assert d["prix"] == 50

    assert isinstance(d["modif"], dict)
    assert d["modif"]["caract"] == "DEF"
    assert d["modif"]["val"] == 2
    assert d["modif"]["source"] == "Armure de cuir"

    assert d["obs"] == "légère"


def test_armure_from_dict():
    d = {
        "ref": "CUIR",
        "label": "Armure de cuir",
        "prix": 50,
        "modif": {"caract": "DEF", "val": 2},
        "obs": "légère",
    }

    a = Armure.from_dict(d)

    assert a.ref == "CUIR"
    assert a.label == "Armure de cuir"
    assert a.prix == 50
    assert isinstance(a.modif, Modificateur)
    assert a.modif.caract == "DEF"
    assert a.modif.val == 2
    # important : source = "" car pas fournie
    assert a.modif.source == ""
    assert a.obs == "légère"


# TEST MODIFICATEUR #


def test_modificateur_default_creation():
    m = Modificateur(caract="DEF", val=2)

    assert m.caract == "DEF"
    assert m.val == 2
    assert m.source == ""


def test_modificateur_to_dict():

    m = Modificateur(
        caract="DEF",
        val=2,
        source="Armure de cuir",
    )

    d = m.to_dict()

    assert isinstance(d, dict)
    assert d["caract"] == "DEF"
    assert d["val"] == 2
    assert d["source"] == "Armure de cuir"


def test_modificateur_from_dict_with_source():
    d = {
        "caract": "DEF",
        "val": 3,
        "source": "Buff",
    }

    m = Modificateur.from_dict(d)

    assert m.caract == "DEF"
    assert m.val == 3
    assert m.source == "Buff"


def test_modificateur_from_dict_without_source():
    d = {
        "caract": "DEF",
        "val": 2,
    }

    m = Modificateur.from_dict(d, external_src="Armure de cuir")

    assert m.caract == "DEF"
    assert m.val == 2
    assert m.source == "Armure de cuir"


def test_modificateur_round_trip():
    m1 = Modificateur(
        caract="DEF",
        val=2,
        source="Armure de cuir",
    )

    d = m1.to_dict()
    m2 = Modificateur.from_dict(d)

    assert m1 == m2


# TEST MODIFICATEURS #


def test_modificateurs_default():
    m = Modificateurs()

    assert isinstance(m.liste_mods, list)
    assert len(m.liste_mods) == 0


def test_modificateurs_add():
    m = Modificateurs()

    mod = Modificateur("DEF", 2)
    m.add(mod)

    assert len(m.liste_mods) == 1
    assert m.liste_mods[0] == mod


def test_modificateurs_to_dict_empty():
    m = Modificateurs()
    d = m.to_dict()

    assert isinstance(d, dict)
    assert "liste_mods" in d
    assert d["liste_mods"] == []


def test_modificateurs_to_dict():
    m = Modificateurs()
    m.add(Modificateur("DEF", 2, "Armure"))
    m.add(Modificateur("DM", 1, "Buff"))

    d = m.to_dict()

    assert len(d["liste_mods"]) == 2

    assert d["liste_mods"][0]["caract"] == "DEF"
    assert d["liste_mods"][1]["caract"] == "DM"


def test_modificateurs_from_dict():
    d = {
        "liste_mods": [
            {"caract": "DEF", "val": 2},
            {"caract": "DM", "val": 1},
        ]
    }

    m = Modificateurs.from_dict(d)

    assert isinstance(m, Modificateurs)
    assert len(m.liste_mods) == 2

    assert m.liste_mods[0].caract == "DEF"
    assert m.liste_mods[1].caract == "DM"


def test_modificateurs_from_dict_missing_key():
    d = {}

    m = Modificateurs.from_dict(d)

    assert isinstance(m, Modificateurs)
    assert len(m.liste_mods) == 0


def test_modificateurs_round_trip():
    m1 = Modificateurs()
    m1.add(Modificateur("DEF", 2, "Armure"))
    m1.add(Modificateur("DM", 1, "Buff"))

    d = m1.to_dict()
    m2 = Modificateurs.from_dict(d)

    assert len(m2.liste_mods) == 2

    assert m2.liste_mods[0].caract == m1.liste_mods[0].caract
    assert m2.liste_mods[1].caract == m1.liste_mods[1].caract


# TEST CAPACITE #


def test_capacite_default_values():
    c = Capacite()

    assert c.ref == "CAPACITE"
    assert c.label == "Nom de Capacité"
    assert c.rang == 1
    assert c.description == "Description de Capacité"

    assert isinstance(c.modifs, Modificateurs)
    assert len(c.modifs.liste_mods) == 0

    assert c.magie is False
    assert c.action == ""


def test_capacite_creation_with_modifs():
    mods = Modificateurs()
    mods.add(Modificateur("DEF", 2, "Rage"))
    mods.add(Modificateur("DM", 3, "Rage"))

    c = Capacite(
        ref="RAGE",
        label="Rage",
        rang=2,
        description="Boost",
        modifs=mods,
    )

    assert c.ref == "RAGE"
    assert c.label == "Rage"
    assert c.rang == 2

    assert len(c.modifs.liste_mods) == 2
    assert c.modifs.liste_mods[0].caract == "DEF"
    assert c.modifs.liste_mods[1].caract == "DM"


def test_capacite_to_dict():
    mods = Modificateurs()
    mods.add(Modificateur("DEF", 2, "Rage"))

    c = Capacite(
        ref="RAGE",
        label="Rage",
        rang=1,
        description="Boost",
        modifs=mods,
    )

    d = c.to_dict()

    assert isinstance(d, dict)

    assert d["ref"] == "RAGE"
    assert d["label"] == "Rage"
    assert d["rang"] == 1
    assert d["description"] == "Boost"

    assert "modifs" in d
    assert "liste_mods" in d["modifs"]

    assert len(d["modifs"]["liste_mods"]) == 1
    assert d["modifs"]["liste_mods"][0]["caract"] == "DEF"
    assert d["modifs"]["liste_mods"][0]["val"] == 2


def test_capacite_from_dict():
    d = {
        "ref": "RAGE",
        "label": "Rage",
        "rang": 1,
        "description": "Boost",
        "modifs": {
            "liste_mods": [
                {"caract": "DEF", "val": 2},
                {"caract": "DM", "val": 3},
            ]
        },
        "magie": True,
        "action": "L",
        "attaque": "FOR",
    }

    c = Capacite.from_dict(d)

    assert c.ref == "RAGE"
    assert c.label == "Rage"
    assert c.rang == 1
    assert c.description == "Boost"

    assert isinstance(c.modifs, Modificateurs)
    assert len(c.modifs.liste_mods) == 2

    assert c.modifs.liste_mods[0].caract == "DEF"
    assert c.modifs.liste_mods[1].caract == "DM"

    assert c.magie is True
    assert c.action == "L"
    assert c.attaque == "FOR"


def test_capacite_round_trip():
    mods = Modificateurs()
    mods.add(Modificateur("DEF", 2, "Rage"))
    mods.add(Modificateur("DM", 3, "Rage"))

    c1 = Capacite(
        ref="RAGE",
        label="Rage",
        rang=1,
        description="Boost",
        modifs=mods,
        magie=True,
        action="L",
        attaque="FOR",
    )

    # Sérialisation
    d = c1.to_dict()

    # Reconstruction
    c2 = Capacite.from_dict(d)

    # Vérifications

    assert c2.ref == c1.ref
    assert c2.label == c1.label
    assert c2.rang == c1.rang
    assert c2.description == c1.description

    # Modificateurs
    assert len(c2.modifs.liste_mods) == 2


# TEST CREATION PERSO #
def test_personnage_creation_basic():
    p = Personnage(
        nom="Test",
        peuple=Peuple.HUMAIN,
        famille=Famille.AVENTURIER,
        profil=Profil.VOLEUR,
        niveau=1,
        caract=Carac(),
    )

    assert p.nom == "Test"
    assert p.niveau == 1
    assert isinstance(p.caract, Carac)


def test_personnage_post_init_ressources():
    p = Personnage(
        nom="Test",
        peuple=Peuple.HUMAIN,
        famille=Famille.AVENTURIER,
        profil=Profil.VOLEUR,
        niveau=1,
        caract=Carac(CONST=2),
    )

    assert isinstance(p.ressources, Ressource)


def test_personnage_add_armure():
    p = Personnage(
        nom="Test",
        peuple=Peuple.HUMAIN,
        famille=Famille.AVENTURIER,
        profil=Profil.VOLEUR,
        niveau=1,
        caract=Carac(),
    )

    armure = Armure(
        ref="CUIR",
        label="Armure de cuir",
        modif=Modificateur("DEF", 2),
    )

    p.ajouter_armure(armure)

    print(p.modificateurs.liste_mods)

    assert len(p.modificateurs.liste_mods) == 1
    assert p.modificateurs.liste_mods[0].caract == "DEF"


def test_personnage_add_capacite_simple():
    p = Personnage(
        nom="Test",
        peuple=Peuple.HUMAIN,
        famille=Famille.AVENTURIER,
        profil=Profil.VOLEUR,
        niveau=1,
        caract=Carac(),
    )

    mods = Modificateurs()
    mods.add(Modificateur("PC", 1, "test"))

    skill = Capacite(
        ref="DIVERSITE_1",
        label="Diversité",
        rang=1,
        description="Ajoute 1 PC",
        modifs=mods,
        magie=False,
    )

    p.ajouter_capacite(skill)

    assert len(p.capacites.list_of_skills) == 1
    assert "DIVERSITE_1" in p.capacites.list_of_skills

    assert len(p.modificateurs.liste_mods) == 1
    assert p.modificateurs.liste_mods[0].caract == "PC"
    assert p.modificateurs.liste_mods[0].val == 1


def test_personnage_add_capacite_magique():
    p = Personnage(
        nom="Test",
        peuple=Peuple.HUMAIN,
        famille=Famille.AVENTURIER,
        profil=Profil.VOLEUR,
        niveau=1,
        caract=Carac(),
    )

    pm_avant = p.ressources.PM

    mods = Modificateurs()
    mods.add(Modificateur("ATK", 1, "test"))

    skill = Capacite(
        ref="SORT_TEST_1",
        label="Petit sort",
        rang=1,
        description="Ajoute 1 ATK",
        modifs=mods,
        magie=True,
    )

    p.ajouter_capacite(skill)

    assert len(p.capacites.list_of_skills) == 1
    assert len(p.spells.list_of_skills) == 1
    assert p.ressources.PM == pm_avant + 1


def test_personnage_add_capacite_no_duplicate():
    p = Personnage(
        nom="Test",
        peuple=Peuple.HUMAIN,
        famille=Famille.AVENTURIER,
        profil=Profil.VOLEUR,
        niveau=1,
        caract=Carac(),
    )

    mods = Modificateurs()
    mods.add(Modificateur("PC", 1, "test"))

    skill = Capacite(
        ref="DIVERSITE_1",
        label="Diversité",
        rang=1,
        description="Ajoute 1 PC",
        modifs=mods,
        magie=False,
    )

    p.ajouter_capacite(skill)
    p.ajouter_capacite(skill)

    assert len(p.capacites.list_of_skills) == 1
    assert len(p.modificateurs.liste_mods) == 1
    assert p.modificateurs.liste_mods[0].caract == "PC"
    assert p.modificateurs.liste_mods[0].val == 1


def test_personnage_add_capacite_symbolic_modif():
    p = Personnage(
        nom="Test",
        peuple=Peuple.HUMAIN,
        famille=Famille.AVENTURIER,
        profil=Profil.VOLEUR,
        niveau=1,
        caract=Carac(FOR=3, CONST=1),
    )

    mods = Modificateurs()
    mods.add(Modificateur("CONST", "FOR", "test"))

    skill = Capacite(
        ref="FORCE_INTERIEURE_1",
        label="Force intérieure",
        rang=1,
        description="Ajoute FOR à CONST",
        modifs=mods,
        magie=False,
    )

    p.ajouter_capacite(skill)

    assert len(p.modificateurs.liste_mods) == 1
    assert p.modificateurs.liste_mods[0].caract == "CONST"
    assert p.modificateurs.liste_mods[0].val == 3


def test_personnage_compute_rollup_modif():
    p = Personnage(
        nom="Test",
        peuple=Peuple.HUMAIN,
        famille=Famille.AVENTURIER,
        profil=Profil.VOLEUR,
        niveau=1,
        caract=Carac(),
    )

    p.modificateurs.add(Modificateur("DEF", 2, "ARMURE:CUIR"))
    p.modificateurs.add(Modificateur("PC", 1, "CAPACITE:DIVERSITE"))
    p.modificateurs.add(Modificateur("DEF", 1, "BUFF:TEST"))

    p.compute_rollup_modif()

    assert isinstance(p.rollup_mod, dict)
    assert p.rollup_mod["DEF"] == 3
    assert p.rollup_mod["PC"] == 1


def test_personnage_from_dict_basic():
    d = {
        "nom": "Lhagva",
        "peuple": Peuple.HUMAIN.value,
        "famille": Famille.COMBATTANT.value,
        "profil": Profil.BARBARE.value,
        "niveau": 1,
        "caract": {
            "AGI": 1,
            "CONST": 2,
            "FOR": 3,
            "PER": 1,
            "CHAR": -1,
            "INT": 0,
            "VOL": 1,
        },
        "equipement": Equipement().to_dict(),
        "voies": {},
        "capacites": Capacites().to_dict(),
        "spells": Capacites().to_dict(),
        "ressources": {
            "PV": 12,
            "DR": [4, 10],  # format YAML relu
            "PM": 1,
            "PC": 2,
            "INIT": 11,
            "DEF": 11,
            "ATK": 3,
            "ATD": 2,
            "ATM": 2,
        },
        "modificateurs": Modificateurs().to_dict(),
        "rollup_mod": {},
    }

    p = Personnage.from_dict(d)

    assert p.nom == "Lhagva"
    assert p.peuple == Peuple.HUMAIN
    assert p.famille == Famille.COMBATTANT
    assert p.profil == Profil.BARBARE
    assert p.niveau == 1

    assert isinstance(p.caract, Carac)
    assert p.caract.FOR == 3

    assert isinstance(p.ressources, Ressource)
    assert p.ressources.PV == 12
    assert isinstance(p.ressources.DR, tuple)
    assert p.ressources.DR == (4, 10)

    assert isinstance(p.equipement, Equipement)
    assert isinstance(p.capacites, Capacites)
    assert isinstance(p.spells, Capacites)
    assert isinstance(p.modificateurs, Modificateurs)

    assert p.rollup_mod == {}


def test_personnage_from_dict_complete():
    armure = Armure(
        ref="VESTE_CUIR",
        label="Veste en Cuir Simple",
        prix=4,
        modif=Modificateur("DEF", 2),
    )

    equipement = Equipement()
    equipement.equiper_armure(armure)

    mods_skill = Modificateurs()
    mods_skill.add(Modificateur("PC", 1, "PEUPLE:HUMAIN:1"))

    skill = Capacite(
        ref="HUMAIN_1",
        label="Diversité",
        rang=1,
        description="Ajoute 1 PC",
        modifs=mods_skill,
        magie=False,
    )

    capacites = Capacites()
    capacites.add_skill(skill)

    modifs_perso = Modificateurs()
    modifs_perso.add(Modificateur("DEF", 2, "ARMURE:VESTE_CUIR"))
    modifs_perso.add(Modificateur("PC", 1, "HUMAIN_1 ; Diversité ; 1"))

    d = {
        "nom": "Lhagva",
        "peuple": Peuple.HUMAIN.value,
        "famille": Famille.COMBATTANT.value,
        "profil": Profil.BARBARE.value,
        "niveau": 1,
        "caract": Carac(
            AGI=1, CONST=2, FOR=3, PER=1, CHAR=-1, INT=0, VOL=1
        ).to_dict(),
        "equipement": equipement.to_dict(),
        "voies": {},
        "capacites": capacites.to_dict(),
        "spells": Capacites().to_dict(),
        "ressources": Ressource(
            PV=12,
            DR=(4, 10),
            PM=1,
            PC=2,
            INIT=11,
            DEF=11,
            ATK=3,
            ATD=2,
            ATM=2,
        ).to_dict(),
        "modificateurs": modifs_perso.to_dict(),
        "rollup_mod": {"DEF": 999, "PC": 999},  # volontairement faux
    }

    p = Personnage.from_dict(d)

    assert p.nom == "Lhagva"
    assert p.peuple == Peuple.HUMAIN

    # équipement
    assert "VESTE_CUIR" in p.equipement.armures
    assert isinstance(p.equipement.armures["VESTE_CUIR"], Armure)
    assert isinstance(
        p.equipement.armures["VESTE_CUIR"].modif, Modificateur
    )

    # capacités
    assert "HUMAIN_1" in p.capacites.list_of_skills
    assert isinstance(p.capacites.list_of_skills["HUMAIN_1"], Capacite)
    assert (
        len(p.capacites.list_of_skills["HUMAIN_1"].modifs.liste_mods)
        == 1
    )
    assert (
        p.capacites.list_of_skills["HUMAIN_1"]
        .modifs.liste_mods[0]
        .caract
        == "PC"
    )

    # modifs perso
    assert len(p.modificateurs.liste_mods) == 2
    assert p.modificateurs.liste_mods[0].caract == "DEF"
    assert p.modificateurs.liste_mods[1].caract == "PC"


def test_personnage_from_dict_recomputes_rollup_mod():
    modifs_perso = Modificateurs()
    modifs_perso.add(Modificateur("DEF", 2, "ARMURE:VESTE_CUIR"))
    modifs_perso.add(Modificateur("DEF", 1, "VOIE:TEST:1"))
    modifs_perso.add(Modificateur("PC", 1, "PEUPLE:HUMAIN:1"))

    d = {
        "nom": "Lhagva",
        "peuple": Peuple.HUMAIN.value,
        "famille": Famille.COMBATTANT.value,
        "profil": Profil.BARBARE.value,
        "niveau": 1,
        "caract": Carac().to_dict(),
        "equipement": Equipement().to_dict(),
        "voies": {},
        "capacites": Capacites().to_dict(),
        "spells": Capacites().to_dict(),
        "ressources": Ressource().to_dict(),
        "modificateurs": modifs_perso.to_dict(),
        "rollup_mod": {"DEF": 999, "PC": 999},  # faux exprès
    }

    p = Personnage.from_dict(d)

    assert p.rollup_mod["DEF"] == 3
    assert p.rollup_mod["PC"] == 1


def test_personnage_from_dict_keeps_saved_rollup_if_no_modificateurs():
    d = {
        "nom": "Test",
        "peuple": Peuple.HUMAIN.value,
        "famille": Famille.AVENTURIER.value,
        "profil": Profil.VOLEUR.value,
        "niveau": 1,
        "caract": Carac().to_dict(),
        "equipement": Equipement().to_dict(),
        "voies": {},
        "capacites": Capacites().to_dict(),
        "spells": Capacites().to_dict(),
        "ressources": Ressource().to_dict(),
        "modificateurs": Modificateurs().to_dict(),
        "rollup_mod": {"DEF": 42},
    }

    p = Personnage.from_dict(d)

    assert p.modificateurs.liste_mods == []
    assert p.rollup_mod == {"DEF": 42}


def test_personnage_round_trip():
    p1 = Personnage(
        nom="Lhagva",
        peuple=Peuple.HUMAIN,
        famille=Famille.COMBATTANT,
        profil=Profil.BARBARE,
        niveau=1,
        caract=Carac(
            AGI=1, CONST=2, FOR=3, PER=1, CHAR=-1, INT=0, VOL=1
        ),
    )

    armure = Armure(
        ref="VESTE_CUIR",
        label="Veste en Cuir Simple",
        prix=4,
        modif=Modificateur("DEF", 2),
    )
    p1.ajouter_armure(armure)

    mods = Modificateurs()
    mods.add(Modificateur("PC", 1, "PEUPLE:HUMAIN:1"))
    skill = Capacite(
        ref="HUMAIN_1",
        label="Diversité",
        rang=1,
        description="Ajoute 1 PC",
        modifs=mods,
    )
    p1.ajouter_capacite(skill)

    p1.compute_rollup_modif()

    d = p1.to_dict()
    p2 = Personnage.from_dict(d)

    assert p2.nom == p1.nom
    assert p2.peuple == p1.peuple
    assert p2.famille == p1.famille
    assert p2.profil == p1.profil
    assert p2.niveau == p1.niveau

    assert p2.caract == p1.caract

    assert p2.ressources.PV == p1.ressources.PV
    assert p2.ressources.DR == p1.ressources.DR

    assert len(p2.equipement.armures) == 1
    assert "VESTE_CUIR" in p2.equipement.armures

    assert "HUMAIN_1" in p2.capacites.list_of_skills
    assert len(p2.modificateurs.liste_mods) == len(
        p1.modificateurs.liste_mods
    )

    assert p2.rollup_mod == p1.rollup_mod
