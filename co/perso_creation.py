from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Tuple
import json
import yaml
from co.perso_data import (
    Peuple,
    Profil,
    Famille,
    DR_PAR_FAMILLE,
    PV_PAR_FAMILLE,
)
from co import bdd_voies as bdd


# ========== Dataclasses de base ==========
@dataclass
class Carac:
    """
    les caractéristiques de base
    """

    AGI: int = 0
    CONST: int = 0
    FOR: int = 0
    PER: int = 0
    CHAR: int = 0
    INT: int = 0
    VOL: int = 0

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Carac:
        """
        Reconstruit un jeu Carac depuis un dict.
        """
        return cls(
            AGI=d.get("AGI", 0),
            CONST=d.get("CONST", 0),
            FOR=d.get("FOR", 0),
            PER=d.get("PER", 0),
            CHAR=d.get("CHAR", 0),
            INT=d.get("INT", 0),
            VOL=d.get("VOL", 0),
        )

    def __str__(self) -> str:
        return str_from_dataclass(self)


@dataclass
class Ressource:
    """
    Les ressources de base (grandeurs recalculées à partir des
    caractéristiques, de l'équipement, etc.).
    """

    PV: int = 0
    DR: Tuple[int, int] = (0, 0)
    PM: int = 0
    PC: int = 0
    INIT: int = 0
    DEF: int = 0
    ATK: int = 0
    ATD: int = 0
    ATM: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Ressource":
        """
        Reconstruit un objet Ressource depuis un dictionnaire.
        """
        dr = d.get("DR", (0, 0))
        if isinstance(dr, list):
            dr = tuple(dr)

        return cls(
            PV=d.get("PV", 0),
            DR=dr,
            PM=d.get("PM", 0),
            PC=d.get("PC", 0),
            INIT=d.get("INIT", 0),
            DEF=d.get("DEF", 0),
            ATK=d.get("ATK", 0),
            ATM=d.get("ATM", 0),
            ATD=d.get("ATD", 0),
        )

    def __str__(self) -> str:
        return str_from_dataclass(self)

    @classmethod
    def from_personnage(cls, p: Personnage) -> Ressource:
        r = cls()
        r._calculer_ressources(p)
        return r

    def _calculer_ressources(self, p: Personnage) -> None:
        """
        Calcule les ressources à partir des caractéristiques
        et du profil du personnage.
        """
        self._calc_def(p)
        self._calc_init(p)
        self._calc_pm(p)
        self._calc_dr(p, DR_PAR_FAMILLE)
        self._calc_pv(p, PV_PAR_FAMILLE)
        self._calc_pc(p)
        self._calcule_attaque(p)

    def _calc_pv(self, p: Personnage, PV_PAR_FAMILLE) -> None:
        """
        Calcule les points de vigueur.
        """
        base = PV_PAR_FAMILLE[p.famille]
        niveau = p.niveau
        const = p.caract.CONST
        pv_total = niveau * (base + const) + base

        self.PV = pv_total

    def _calc_dr(self, p: Personnage, DR_PAR_FAMILLE) -> None:
        """
        Calcule le nombre de DR et leur valeur max (nombre, valeur max).
        """
        valeur_max = DR_PAR_FAMILLE[p.famille]
        const = p.caract.CONST
        nombre = 2 + const

        if p.famille == Famille.MYSTIQUE:
            nombre += 1

        nombre = max(nombre, 0)

        self.DR = (nombre, valeur_max)

    def _calc_pc(self, p: Personnage) -> None:
        """
        Calcule les points de chance.
        """
        char = p.caract.CHAR
        nombre = 2 + char

        if p.famille == Famille.AVENTURIER:
            nombre += 1

        if p.peuple == Peuple.HUMAIN:
            nombre += 1

        self.PC = nombre

    def _calc_pm(self, p: Personnage) -> None:
        """
        Calcule les points de mana.
        """
        vol = p.caract.VOL
        self.PM = vol

    def _calc_init(self, p: Personnage) -> None:
        """
        Calcule l'initiative.
        """
        per = p.caract.PER
        self.INIT = per + 10

    def _calc_def(self, p: Personnage) -> None:
        """
        Calcule la défense.
        """
        agi = p.caract.AGI
        self.DEF = agi + 10

    def _calcule_attaque(self, p: Personnage) -> None:
        """
        Calcule attaque au contact, à distance et magique.
        """
        niveau = p.niveau
        const = p.caract.CONST
        agi = p.caract.AGI
        vol = p.caract.VOL

        self.ATK = niveau + const
        self.ATD = niveau + agi
        self.ATM = niveau + vol


@dataclass
class Modificateur:
    """Un modificateur est un bonus / malus
    à appliquer à une carac ou resssource.
    qui peeut venir d'une compétence, d'un équipement.
    Il se caracérise par la caract/ressource en question (label),
    la valeur à appliquer (val), la source (voie, équipement, etc)
    et éventuellement un commentaire.
    """

    caract: str  # ex: "DEF"
    val: int | str  # +3,
    source: str = ""  # ex: "Armure de cuir", "Buff: Peau de pierre"

    def to_dict(self) -> Dict[str, Any]:
        """
        Sérialise un Modificateur vers un dict JSON-safe.
        """
        return {
            "caract": self.caract,
            "val": self.val,
            "source": self.source,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any], external_src="") -> "Modificateur":
        source = d.get("source", external_src)
        return Modificateur(
            caract=d.get("caract", ""),
            val=d.get("val", 0),
            source=source,
        )


# ========== Capacités / Équipement ==========
@dataclass
class Arme:
    """dataclass pour les Armes :
    ref (nom normalisé), label (nom courant),
    DM,
    type attaque : contact, distance,
    type de dégat : contondant, perforant, etc,
    prix,
    portée si distance,
    observation facultative
    Les Armes seront gérées dans le Containers Equipement
    Le catalogue des Armes est un YAML.
    """

    ref: str = "ARME"
    label: str = "description ARME"
    DM: str = "1d6"
    type_attaque: str = ""
    type_degat: str = ""
    prix: int = 0
    portee: int = 0
    obs: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise une arme vers un dict JSON-safe."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Arme":
        """Reconstruit une Arme depuis un dict."""
        return cls(
            ref=d.get("ref", "ARME"),
            label=d.get("label", "description d'une arme"),
            DM=d.get("DM", "1d6"),
            type_attaque=d.get("type_attaque", ""),
            type_degat=d.get("type_degat", ""),
            prix=d.get("prix", 0),
            portee=d.get("portee", 0),
            obs=d.get("obs", ""),
        )


@dataclass
class Armure:
    """dataclass pour les Armures :
    ref (nom normalisé), label (nom courant),
    prix,
    modif : modificateur de DEF,
    observation facultative
    Les Armures seront gérées dans le Containers Equipement
    Le catalogue des Armures est un YAML.
    """

    ref: str = "ARMURE"
    label: str = "Description d'Armure"
    prix: int = 0
    modif: Modificateur = field(
        default_factory=lambda: Modificateur(caract="DEF", val=0)
    )
    obs: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise une armure vers un dict JSON-safe."""
        return {
            "ref": self.ref,
            "label": self.label,
            "prix": self.prix,
            "modif": self.modif.to_dict(),
            "obs": self.obs,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Armure":
        """Reconstruit une armure depuis un dict."""
        return cls(
            ref=d.get("ref", "ARMURE"),
            label=d.get("label", "Description d'Armure"),
            prix=d.get("prix", 0),
            modif=Modificateur.from_dict(d.get("modif", {})),
            obs=d.get("obs", ""),
        )


@dataclass
class Capacite:
    ref: str = "CAPACITE"
    label: str = "Nom de Capacité"
    rang: int = 1
    description: str = "Description de Capacité"
    modifs: Modificateurs = field(
        default_factory=lambda: Modificateurs()
    )
    magie: bool = False
    action: str = ""
    attaque: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ref": self.ref,
            "label": self.label,
            "rang": self.rang,
            "description": self.description,
            "modifs": self.modifs.to_dict(),
            "magie": self.magie,
            "action": self.action,
            "attaque": self.attaque,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Capacite":
        return cls(
            ref=d.get("ref", "CAPACITE"),
            label=d.get("label", "Nom de Capacité"),
            rang=d.get("rang", 1),
            description=d.get("description", "Description de Capacité"),
            modifs=Modificateurs.from_dict(d.get("modifs", {})),
            magie=d.get("magie", False),
            action=d.get("action", ""),
            attaque=d.get("attaque", ""),
        )


# ===== Containers =====
@dataclass
class Equipement:
    """
    gère la liste des armes, armures sous forme de Dict
    gère aussi un sac pour le reste de l'équipement (Dict format libre)
    """

    armes: Dict[str, Arme] = field(default_factory=dict)
    armures: Dict[str, Armure] = field(default_factory=dict)
    sac: Dict[str, Any] = field(default_factory=dict)

    def equiper_arme(self, arme: Arme) -> None:
        """
        Ajoute une arme à l'équipement du personnage.
        Une seule arme ajoutée pour une ref donnée  (évite les doublons)
        """
        self.armes[arme.ref] = arme

    def equiper_armure(self, armure: Armure) -> None:
        """
        Ajoute une arme à l'équipement du personnage.
        Une seule armure ajoutée pour une ref donnée (évite les doublons)
        """
        self.armures[armure.ref] = armure

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'équipement en dict JSON-safe."""
        return {
            "armes": {
                k: v.to_dict() for k, v in (self.armes or {}).items()
            },
            "armures": {
                k: v.to_dict() for k, v in (self.armures or {}).items()
            },
            "sac": self.sac or {},
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Equipement":
        """Désérialise depuis un dict vers Equipement."""
        armes = {
            k: Arme.from_dict(v) for k, v in d.get("armes", {}).items()
        }
        armures = {
            k: Armure.from_dict(v)
            for k, v in d.get("armures", {}).items()
        }
        sac = d.get("sac", {})
        return Equipement(armes=armes, armures=armures, sac=sac)


@dataclass
class Capacites:
    """
    gère la liste des capacités connues sous forme d'un dict de Capacités
    """

    # TODO : peut être simplifié ?

    list_of_skills: Dict[str, Capacite] = field(default_factory=dict)

    def add_skill(self, skill: Capacite) -> None:
        """
        Ajoute une skill à la liste des capacités connues.
        Une seule skill ajoutée pour une ref donnée (évite les doublons)
        """

        if (
            skill.ref not in self.list_of_skills.keys()
        ):  # TODO : surement pas utile, à tester...
            self.list_of_skills[skill.ref] = skill

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le conteneur vers un dict JSON-safe."""
        return {
            "list_of_skills": {
                k: v.to_dict()
                for k, v in (self.list_of_skills or {}).items()
            }
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Capacites":
        """Reconstruit le conteneur depuis un dict."""
        los = {
            k: Capacite.from_dict(v)
            for k, v in d.get("list_of_skills", {}).items()
        }
        return Capacites(list_of_skills=los)


@dataclass
class Modificateurs:
    """
    liste de modificateurs.
    """

    liste_mods: List[Modificateur] = field(default_factory=list)

    def add(self, mod: Modificateur):
        """ajoute un modificateur"""
        self.liste_mods.append(mod)

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le conteneur vers un dict JSON-safe."""
        return {
            "liste_mods": [m.to_dict() for m in (self.liste_mods or [])]
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Modificateurs":
        """Reconstruit le conteneur depuis un dict."""
        return Modificateurs(
            liste_mods=[
                Modificateur.from_dict(m)
                for m in d.get("liste_mods", [])
            ]
        )


# ========== Personnage ==========
@dataclass
class Personnage:
    """classe principale : Personnage
    - nom
    - peuple, famille, profil: ex 'Humain Aventurier Voleur"
    - niveau : int débutant à 1
    - caract, ressources : stats du perso
    - voies: résumé des voies choisies (pour affichage)
    - capacites : liste des capacités apprises par les voies
    - spells : container spécialisé des capacités magiques
    - modificateurs :
        containter
        de tous les modificateurs conférés par les armes, voies, etc
    - rollup_mod : aggrégation de mod sous forme de dict.

    Le calcul des ressources etc, se fait actuellement à l'initialisation du perso.
    """

    nom: str
    peuple: Peuple
    famille: Famille
    profil: Profil
    niveau: int
    caract: Carac
    equipement: Equipement = field(default_factory=Equipement)
    voies: Dict[str, int] = field(default_factory=dict)
    capacites: Capacites = field(default_factory=Capacites)
    spells: Capacites = field(default_factory=Capacites)
    # TODO : voir si on laisse deux containers de Skills
    ressources: Ressource = field(default_factory=Ressource)
    modificateurs: Modificateurs = field(default_factory=Modificateurs)
    rollup_mod: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """calcule les ressources"""
        # TODO : penser à recalculer les ressources si montée de niveau
        self.ressources = Ressource.from_personnage(self)
        if len(self.modificateurs.liste_mods) > 0:
            self.rollup_mod = self.compute_rollup_modif()

    def __str__(self) -> str:
        ln1 = f"{self.nom} : {self.peuple} {self.profil}, niveau {self.niveau}"
        ln2 = f"{self.caract}"
        ln3 = f"{self.ressources}"
        return ln1 + "\n" + ln2 + "\n" + ln3

    # — Équipement
    def ajouter_arme(self, arme: Arme) -> None:
        """ajouter une arme"""
        self.equipement.equiper_arme(arme)

    def ajouter_armure(self, armure: Armure) -> None:

        self.equipement.equiper_armure(armure)

        # supprimer les anciens modifs d'armure
        self.modificateurs.liste_mods = [
            m
            for m in self.modificateurs.liste_mods
            if not m.source.startswith("ARMURE:")
        ]

        modif = Modificateur(
            caract=armure.modif.caract,
            val=armure.modif.val,
            source=f"ARMURE:{armure.ref}",
        )

        self.modificateurs.add(modif)

    def ajouter_capacite(self, skill: Capacite) -> None:
        """Ajoute une capacité au personnage.

        - ajoute la capacité si elle n'est pas déjà connue
        - ajoute un PM si c'est un sort
        - résout les modificateurs symboliques éventuels
        - injecte les modificateurs actifs dans le personnage
        """

        if self._skill_already_learned(skill):
            return

        self.capacites.add_skill(skill)

        if skill.magie:
            self.spells.add_skill(skill)
            self.ressources.PM += 1

        if (
            skill.modifs is not None
            and len(skill.modifs.liste_mods) > 0
        ):
            resolved_mods = self._resolve_modifs_capacite(skill.modifs)

            source = " ; ".join(
                [skill.ref, skill.label, str(skill.rang)]
            )

            for m in resolved_mods.liste_mods:
                self.modificateurs.add(
                    Modificateur(
                        caract=m.caract,
                        val=m.val,
                        source=source,
                    )
                )

    def compute_rollup_modif(self) -> Dict[str, int]:
        """Agrège les modificateurs actifs par caractéristique / ressource."""
        rollup = {}

        for md in self.modificateurs.liste_mods:
            if not isinstance(md.val, int):
                raise ValueError(
                    f"Modificateur non résolu détecté : {md.caract}={md.val!r}"
                )

            rollup[md.caract] = rollup.get(md.caract, 0) + md.val

        self.rollup_mod = rollup
        return rollup

    def _skill_already_learned(self, skill: Capacite):
        """
        vérifie si une skill est déjà connue
        (pour éviter d'ajouter ses modificateurs plusieurs fois)
        """
        sk_name, sk_rang = (skill.ref, skill.rang)
        fl = False
        for n, r in self.capacites.list_of_skills.items():
            if n == sk_name and r.rang == sk_rang:
                fl = True
        return fl

    def _resolve_modifs_capacite(
        self, modifs: Modificateurs
    ) -> Modificateurs:
        """
        Résout les modificateurs d'une capacité pour ce personnage.

        Remplace les valeurs symboliques ("AGI", "FOR", etc.)
        par les valeurs réelles des caractéristiques du personnage.

        Retourne un nouveau conteneur, sans modifier la capacité source.
        """
        out = Modificateurs()

        for m in modifs.liste_mods:
            val = m.val

            if isinstance(val, str) and val in {
                "AGI",
                "CONST",
                "FOR",
                "PER",
                "CHAR",
                "INT",
                "VOL",
            }:
                val = getattr(self.caract, val)

            out.add(
                Modificateur(
                    caract=m.caract,
                    val=val,
                    source=m.source,
                )
            )

        return out

    # --- ajouter une liste de voies manuelleemnt
    def set_skill_from_dict(
        self, dict_voies: Dict[str, int], bd_path="data/database.db"
    ):
        """
        ajoute les skills par la voie + rang que l'on va chercher dans leur bdd
        exemple :
        {"VOIE_DE_L_AIR": 1, "VOIE_DU_BERSERK": 1}
        """
        # TODO : pour le moment ne fonctionne que pour les capacités de classe
        self.voies = dict(dict_voies)
        for voie_id, voie_rang in dict_voies.items():
            label, description, modif, is_magic, action, attaque = (
                bdd.get_cls_capacity_details(
                    bd_path, voie_id, voie_rang
                )
            )
            modif_dict = json.loads(modif)
            skill = Capacite(
                ref=voie_id,
                label=label,
                rang=voie_rang,
                description=description,
                modif=modif_dict,
                magie=is_magic,
                action=action,
                attaque=attaque,
            )
            self.ajouter_capacite(skill)

    # === Utilitaires ===

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nom": self.nom,
            "peuple": self.peuple.value,
            "famille": self.famille.value,
            "profil": self.profil.value,
            "niveau": self.niveau,
            "caract": self.caract.to_dict(),
            "equipement": self.equipement.to_dict(),
            "voies": self.voies,
            "capacites": self.capacites.to_dict(),
            "spells": self.spells.to_dict(),
            "ressources": self.ressources.to_dict(),
            "modificateurs": self.modificateurs.to_dict(),
            "rollup_mod": self.rollup_mod,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Personnage":
        p = cls(
            nom=d.get("nom", ""),
            peuple=Peuple(d.get("peuple", Peuple.HUMAIN.value)),
            famille=Famille(d.get("famille", Famille.AVENTURIER.value)),
            profil=Profil(d.get("profil", Profil.VOLEUR.value)),
            niveau=d.get("niveau", 1),
            caract=Carac.from_dict(d.get("caract", {})),
            equipement=Equipement.from_dict(d.get("equipement", {})),
            voies=d.get("voies", {}),
            capacites=Capacites.from_dict(d.get("capacites", {})),
            spells=Capacites.from_dict(d.get("spells", {})),
            modificateurs=Modificateurs.from_dict(
                d.get("modificateurs", {})
            ),
            # valeurs provisoires, car __post_init__ va recalculer
            ressources=Ressource(),
            rollup_mod={},
        )

        # restaurer ensuite l'état sauvegardé
        p.ressources = Ressource.from_dict(d.get("ressources", {}))

        # soit on fait confiance au YAML...
        # p.rollup_mod = d.get("rollup_mod", {})

        # ... soit on préfère recalculer depuis les modificateurs actifs
        if p.modificateurs.liste_mods:
            p.rollup_mod = p.compute_rollup_modif()
        else:
            p.rollup_mod = d.get("rollup_mod", {})

        return p


# ========== Helpers sérialisation d'Enum ==========


def str_from_dataclass(obj: Any) -> str:
    data = asdict(obj)
    parts = [f"{k} = {data[k]}" for k in data.keys()]
    return " | ".join(parts)


# ========== Data Loaders  ==========


def ppl_skill_from_bdd(
    bdd_path, peuple_id: str, voie_rang: int
) -> Capacite:
    """Crée un objet Capacite de peuple à partir de la BDD."""

    label, description, modif, is_magic, action, attaque = (
        bdd.get_ppl_capacity_details(bdd_path, peuple_id, voie_rang)
    )

    modif_dict = json.loads(modif) if modif else {}

    mods = Modificateurs()
    for caract, valeur in modif_dict.items():
        mods.add(
            Modificateur(
                caract=caract,
                val=valeur,
                source=f"PEUPLE:{peuple_id}:{voie_rang}",
            )
        )

    skill = Capacite(
        ref=f"{peuple_id}_{voie_rang}",
        label=label,
        rang=voie_rang,
        description=description,
        modifs=mods,
        magie=bool(is_magic),
        action=action or "",
        attaque=attaque or "",
    )

    return skill


def classe_skill_from_bdd(
    bdd_path, voie_id: str, voie_rang: int
) -> Capacite:
    """Crée un objet Capacite de voie à partir de la BDD."""

    label, description, modif, is_magic, action, attaque = (
        bdd.get_cls_capacity_details(bdd_path, voie_id, voie_rang)
    )

    modif_dict = json.loads(modif) if modif else {}

    mods = Modificateurs()
    for caract, valeur in modif_dict.items():
        mods.add(
            Modificateur(
                caract=caract,
                val=valeur,
                source=f"VOIE:{voie_id}:{voie_rang}",
            )
        )

    skill = Capacite(
        ref=f"{voie_id}_{voie_rang}",
        label=label,
        rang=voie_rang,
        description=description,
        modifs=mods,
        magie=bool(is_magic),
        action=action or "",
        attaque=attaque or "",
    )

    return skill


def load_materiel(path: str, sub_set: str = "ARMES") -> Dict[str, Any]:
    """charge le catalogue des ARMES et des ARMURES qui se trouve dans un YAML

    Args:
        path (str): le YAML
        sub_set (str, optional): Specifier 'ARMES' ou 'ARMURES'.
        Defaults to "ARMES".

    Raises:
        ValueError: _description_

    Returns:
        Dict[str, Any]: Dict des Armes ou ARMURES
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    sections = {"ARMES": Arme, "ARMURES": Armure}
    if sub_set not in sections:
        raise ValueError(
            f"Section inconnue '{sub_set}'. Attendu: {list(sections)}"
        )
    section_data = section_data = data.get(sub_set, {})
    cls_ = sections[sub_set]
    out: Dict[str, Any] = {}
    for name, props in section_data.items():
        props = dict(props)
        props["ref"] = name
        out[name] = cls_.from_dict(props)
    return out
