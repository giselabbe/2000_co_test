# personnage.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Tuple
from enum import Enum

# ========== Peuples, Familles et Classes  ==========


class Peuple(Enum):
    HUMAIN = "Humain"
    NAIN = "Nain"
    ELFE_HAUT = "Elfe Haut"
    DEMI_ELFE = "Demi-Elfe"
    ELFE_SYLVAIN = "Elfe Sylvain"
    DEMI_ORC = "Demi-Orc"
    GNOME = "Gnome"
    HALFELIN = "Halfelin"

    def __str__(self) -> str:
        return self.value


class Famille(Enum):
    AVENTURIER = "Aventurier"
    COMBATTANT = "Combattant"
    MAGE = "Mage"
    MYSTIQUE = "Mystique"

    def __str__(self) -> str:
        return self.value


class Profil(Enum):
    ARQUEBUSIER = "Arquebusier"
    BARDE = "Barde"
    RODEUR = "Rôdeur"
    VOLEUR = "Voleur"
    BARBARE = "Barbare"
    CHEVALIER = "Chevalier"
    GUERRIER = "Guerrier"
    ENSORCELEUR = "Ensorceleur"
    FORGESORT = "Forgesort"
    MAGICIEN = "Magicien"
    SORCIER = "Sorcier"
    DRUIDE = "Druide"
    MOINE = "Moine"
    PRETRE = "Prêtre"

    def __str__(self) -> str:
        return self.value


# — Famille ↔ Profils
PROFILS_PAR_FAMILLE: Dict[Famille, Tuple[Profil, ...]] = {
    Famille.AVENTURIER: (
        Profil.ARQUEBUSIER,
        Profil.BARDE,
        Profil.RODEUR,
        Profil.VOLEUR,
    ),
    Famille.COMBATTANT: (
        Profil.BARBARE,
        Profil.CHEVALIER,
        Profil.GUERRIER,
    ),
    Famille.MAGE: (
        Profil.ENSORCELEUR,
        Profil.FORGESORT,
        Profil.MAGICIEN,
        Profil.SORCIER,
    ),
    Famille.MYSTIQUE: (Profil.DRUIDE, Profil.MOINE, Profil.PRETRE),
}
FAMILLE_PAR_PROFIL: Dict[Profil, Famille] = {
    p: f for f, ps in PROFILS_PAR_FAMILLE.items() for p in ps
}

# — Valeurs de base par famille (exemple simple ; ajuste selon tes règles)
PV_PAR_FAMILLE: Dict[Famille, int] = {
    Famille.AVENTURIER: 4,
    Famille.COMBATTANT: 5,
    Famille.MAGE: 3,
    Famille.MYSTIQUE: 4,
}
DR_PAR_FAMILLE: Dict[Famille, int] = {
    Famille.AVENTURIER: 8,
    Famille.COMBATTANT: 10,
    Famille.MAGE: 6,
    Famille.MYSTIQUE: 8,
}
