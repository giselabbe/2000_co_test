import pytest
from co.perso_creation import Carac, Ressource
from co.perso_data import Peuple, Famille

# PREPARATION #
from dataclasses import dataclass


@dataclass
class FakeCarac:
    AGI: int = 0
    CONST: int = 0
    PER: int = 0
    VOL: int = 0
    CHAR: int = 0


from dataclasses import dataclass


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
