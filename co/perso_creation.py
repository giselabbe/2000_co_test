from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Tuple
import json
import yaml
from co.perso_data import Peuple, Profil, Famille, DR_PAR_FAMILLE, PV_PAR_FAMILLE
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

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Carac:
        """
        Reconstruit un jeu Carac depuis un dict.
        """
        return Modificateur(
            AGI=d["AGI"],
            CONST=d["CONST"],
            FOR=d["FOR"],
            PER=d["PER"],
            CHAR=d["CHAR"],
            INT=d["INT"],
            VOL=d["VOL"],
        )

    def __str__(self) -> str:
        return str_from_dataclass(self)


@dataclass
class Ressource:
    """
    les ressources de base (grandeurs recalculées à partir des caract,
     équipement, etc)
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

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Carac:
        """
        Reconstruit un jeu Carac depuis un dict.
        """
        return Modificateur(
            PV=d["PV"],
            DR=d["DR"],
            PM=d["PM"],
            PC=d["PC"],
            INIT=d["INIT"],
            DEF=d["DEF"],
            ATK=d["ATK"],
            ATM=d["ATM"],
            ATD=d["ATD"],
        )

    def __str__(self) -> str:
        return str_from_dataclass(self)

    def calculer_ressources(self, p: Personnage):
        """
        permet de calculer les ressources
        à partir des caractéristiques et du profil de joueur
        """
        self._calc_def(p)
        self._calc_init(p)
        self._calc_pm(p)
        self._calc_dr(p, DR_PAR_FAMILLE)
        self._calc_pv(p, PV_PAR_FAMILLE)
        self._calc_pc(p)
        self._calcule_attaque(p)

    def _calc_pv(self, p: Personnage, PV_PAR_FAMILLE):
        """
        calcule les points de vigueur
        """
        base = PV_PAR_FAMILLE[p.famille]
        niveau = p.niveau
        const = p.caract.CONST
        pv_total = niveau * (base + const) + base

        self.PV = pv_total

    def _calc_dr(self, p: Personnage, DR_PAR_FAMILLE):
        """
        calcule le nombre de DR et leur valeur max (nbre, valeur max)
        """
        valeur_max = DR_PAR_FAMILLE[p.famille]
        const = p.caract.CONST
        nombre = 2 + const

        if p.famille == Famille.MYSTIQUE:
            nombre = nombre + 1

        nombre = max(nombre, 0)

        self.DR = (nombre, valeur_max)

    def _calc_pc(self, p: Personnage):
        """
        calcule les points de chance
        """
        char = p.caract.CHAR
        nombre = 2 + char

        if p.famille == Famille.AVENTURIER:
            nombre = nombre + 1

        if p.peuple == Peuple.HUMAIN:
            nombre = nombre + 1

        self.PC = nombre

    def _calc_pm(self, p: Personnage):
        """
        calcule les points de mana"""

        vol = p.caract.VOL
        self.PM = vol

    def _calc_init(self, p: Personnage):
        """
        calcule initiative
        """
        per = p.caract.PER
        self.INIT = per + 10

    def _calc_def(self, p: Personnage) -> int:
        """
        calcule défense
        """
        agi = p.caract.AGI
        self.DEF = agi + 10

    def _calcule_attaque(self, p: Personnage):
        """
        calcule (attaque contact, attaque à distance, attaque magique)
        """
        niveau = p.niveau
        const = p.caract.CONST
        agi = p.caract.AGI
        vol = p.caract.VOL

        self.ATK, self.ATD, self.ATM = (niveau + const, niveau + agi, niveau + vol)


@dataclass
class Modificateur:
    """Un modificateur est un bonus / malus
    à appliquer à une carac ou resssource.
    qui peeut venir d'une compétence, d'un équipement.
    Il se caracérise par la caract/ressource en question (label),
    la valeur à appliquer (val), la source (voie, équipement, etc)
    et éventuellement un commentaire.
    """

    label: str  # ex: "DEF"
    val: int  # +3,
    source: str  # ex: "Armure de cuir", "Buff: Peau de pierre"
    comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """
        Sérialise un Modificateur vers un dict JSON-safe.
        """
        return {
            "label": self.label,
            "val": self.val,
            "source": self.source,
            "comment": self.comment,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any], external_src="") -> "Modificateur":
        """
        Reconstruit un Modificateur depuis un dict.
        """
        if "source" not in d.keys():
            source = external_src
        else:
            source = d["source"]
        return Modificateur(
            label=d["label"],
            val=d["val"],
            source=source,
            comment=d.get("comment", ""),
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

    ref: str
    label: str
    DM: str
    type_attaque: str
    type_degat: str
    prix: int
    portee: int = 0
    obs: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise une arme vers un dict JSON-safe."""
        return {
            "ref": self.ref,
            "label": self.label,
            "DM": self.DM,
            "type_attaque": self.type_attaque,
            "type_degat": self.type_degat,
            "prix": self.prix,
            "portee": self.portee,
            "obs": self.obs,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Arme":
        """Reconstruit une Arme depuis un dict."""
        return Arme(
            ref=d["ref"],
            label=d["label"],
            DM=d["DM"],
            type_attaque=d["type_attaque"],
            type_degat=d["type_degat"],
            prix=d["prix"],
            portee=d["portee"],
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

    ref: str
    label: str
    prix: int
    modif: Modificateurs = field(default_factory=Modificateur)
    obs: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise une armure vers un dict JSON-safe."""
        return {
            "ref": self.ref,
            "label": self.label,
            "prix": self.prix,
            "modif": self.modif,
            "obs": self.obs,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Armure":
        """Reconstruit une Armure depuis un dict."""
        return Armure(
            ref=d["ref"],
            label=d["label"],
            prix=d["prix"],
            modif=d.get("modif", {}),
            obs=d.get("obs", ""),
        )


@dataclass
class Capacite:
    """dataclass pour les capacitées apprises par les Voies, profil ou peuple.
    Inclut les sorts.

    ref (nom normalisé), label (nom courant),
    rang
    description
    modifs: un objet Modificateurs
    magie : vrai / faux (permet de maj PM)
    action : type action associé (A, M, L, G)
    attaque : caract attaque associée pour les sorts
    Le catalogue des Capacités est gérées par une base de données
    """

    ref: str
    label: str
    rang: int
    description: str
    modif: Modificateurs = field(default_factory=Modificateur)
    magie: bool = False
    action: str = ""
    attaque: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise une capacité vers un dict JSON-safe."""
        return {
            "ref": self.ref,
            "label": self.label,
            "rang": self.rang,
            "description": self.description,
            "modif": self.modif.to_dict(),
            "magie": self.magie,
            "action": self.action,
            "attaque": self.attaque,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Capacite":
        """Reconstruit une Capacite depuis un dict."""
        return Capacite(
            ref=d["ref"],
            label=d["label"],
            rang=d["rang"],
            description=d.get("description", ""),
            modif=Modificateurs.from_dict(d.get("modif"), {}),
            magie=d.get("magie", 0),
            action=d.get("action", None),
            attaque=d.get("attaque", None),
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
            "armes": {k: v.to_dict() for k, v in (self.armes or {}).items()},
            "armures": {k: v.to_dict() for k, v in (self.armures or {}).items()},
            "sac": self.sac or {},
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Equipement":
        """Désérialise depuis un dict vers Equipement."""
        armes = {k: Arme.from_dict(v) for k, v in d.get("armes", {}).items()}
        armures = {k: Armure.from_dict(v) for k, v in d.get("armures", {}).items()}
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
                k: v.to_dict() for k, v in (self.list_of_skills or {}).items()
            }
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Capacites":
        """Reconstruit le conteneur depuis un dict."""
        los = {k: Capacite.from_dict(v) for k, v in d.get("list_of_skills", {}).items()}
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
        return {"liste_mods": [m.to_dict() for m in (self.liste_mods or [])]}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Modificateurs":
        """Reconstruit le conteneur depuis un dict."""
        return Modificateurs(
            liste_mods=[Modificateur.from_dict(m) for m in d.get("liste_mods", [])]
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
    - mod : containter de tous les modificateurs conférés par les armes, voies, etc
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
    mod: Modificateurs = field(default_factory=Modificateurs)
    rollup_mod: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """calcule les ressources"""
        # TODO : penser à recalculer les ressources si montée de niveau
        self.ressources.calculer_ressources(self)
        if len(self.mod.liste_mods) > 0:
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
        """ajouter une armure et le modificateur de DEF associé"""
        self.equipement.equiper_armure(armure)
        # TODO : vérifier si on n'ajoute pas plusieurs fois le modif de DEF

        modif = Modificateur(
            label=armure.modif["label"],
            val=armure.modif["val"],
            source=armure.label,
        )
        self.mod.add(modif)

    def ajouter_capacite(self, skill: Capacite):
        """ajoute une skill
        ajoute un PM si c'est un sort
        """
        if not self._skill_already_learned(skill):
            self.capacites.add_skill(skill)
            if skill.magie == 1:
                self.spells.add_skill(skill)
                self.ressources.PM = self.ressources.PM + 1

            dict_modif = self._update_modif_variable(skill.modif)

            for k, v in dict_modif.items():
                modif = Modificateur(label=k, val=v, source=skill.ref)
                self.mod.add(modif)

    def compute_rollup_modif(self):
        """une fois les modifs aggrégés on les applique"""

        rollup = {}
        for md in self.mod.liste_mods:
            if md.label in rollup.keys():
                rollup[md.label] = md.val + rollup[md.label]
            else:
                rollup[md.label] = md.val

        self.rollup_mod = rollup

    def _skill_already_learned(self, skill: Capacite):
        """
        vérifie si une skill est déjà connue
        (pour éviter d'ajouter ses modificateurs plusieurs fois)
        """
        (sk_name, sk_rang) = (skill.ref, skill.rang)
        fl = False
        for n, r in self.capacites.list_of_skills.items():
            if n == sk_name and r.rang == sk_rang:
                fl = True
        return fl

    def _update_modif_variable(self, modif_variable):
        """
        remplace la valeur symbolique d'un modificateur
        (par ex {'PV': 'FOR'}) par la valeur réelle
        cela peut se produire pour les Capacités seulement.
        """
        md = modif_variable
        for k, v in md.items():
            if v in ["AGI", "CONST", "FOR", "PER", "CHAR", "INT", "VOL"]:
                v_updated = getattr(self.caract, v)
                md[k] = v_updated
        return md

    # --- ajouter une liste de voies manuelleemnt
    def set_skill_from_dict(
        self, dict_voies: Dict[str, int], bd_path="data/database.db"
    ):
        """
        ajoute les skills par la voie + rang que l'on va chercher dans leur bdd
        exemple :
        {"VOIE_DE_L_AIR": 1, "VOIE_DU_BERSERK": 1}
        """
        # TODO : pour le moment ne fonctionne que pour les capacités de classe, pas de peuple
        self.voies = dict(dict_voies)
        for voie_id, voie_rang in dict_voies.items():
            (label, description, modif, is_magic, action, attaque) = (
                bdd.get_cls_capacity_details(bd_path, voie_id, voie_rang)
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
            "mod": self.mod.to_dict(),
            "rollup_mod": self.rollup_mod,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Personnage":
        return Personnage(
            nom=d["nom"],
            peuple=Peuple(d["peuple"]),
            famille=Famille(d["famille"]),
            profil=Profil(d["profil"]),
            niveau=d["niveau"],
            caract=Carac.from_dict(d["caract"]),
            equipement=Equipement.from_dict(d["equipement"]),
            voies=d.get("voies", {}),
            capacites=Capacites.from_dict(d["capacites"]),
            spells=Capacites.from_dict(d["spells"]),
            ressources=Ressource.from_dict(d["ressources"]),
            mod=Modificateurs.from_dict(d["mod"]),
            rollup_mod=d.get("rollup_mod", {}),
        )


# ========== Helpers sérialisation d'Enum ==========


def str_from_dataclass(obj: Any) -> str:
    data = asdict(obj)
    parts = [f"{k} = {data[k]}" for k in data.keys()]
    return " | ".join(parts)


# ========== Data Loaders  ==========


def ppl_skill_from_bdd(bdd_path, peuple_id: str, rang: int):
    """crée un Obket Capacité de Peuple à partir du nom de Peuple et rang choisi
    Args:
        bdd_path (bdd sqlite): bdd des capacités
        peuple_id (_type_): peuple format de réf (ex 'HUMAIN)
        rang (_type_): rang

    Returns:
        Capacité: la capacité
    """
    # TODO : ajouter msg si pas trouvé

    (label, description, modif, is_magic, action, attaque) = (
        bdd.get_ppl_capacity_details(bdd_path, peuple_id, rang)
    )
    modif_dict = json.loads(modif)
    skill = Capacite(
        ref=peuple_id,
        label=label,
        rang=rang,
        description=description,
        modif=Modificateur.from_dict(
            modif_dict, external_src=f"{peuple_id} - rang {rang} - {label}"
        ),
        magie=is_magic,
        action=action,
        attaque=attaque,
    )
    return skill


def classe_skill_from_bdd(bdd_path, voie_id, rang):
    """crée un Obket Capacité de Voie à partir du nom de Peuple et rang choisi
    Args:
        bdd_path (bdd sqlite): bdd des capacités
        voie_id (_type_): peuple format de réf (ex 'VOIE_DE_LAIR)
        rang (_type_): rang

    Returns:
        Capacité: la capacité
    """
    # TODO : ajouter msg si pas trouvé

    (label, description, modif, is_magic, action, attaque) = (
        bdd.get_cls_capacity_details(bdd_path, voie_id, rang)
    )
    if modif is not None:
        modif = json.loads(modif)
    skill = Capacite(
        ref=voie_id,
        label=label,
        rang=rang,
        description=description,
        modif=Modificateur.from_dict(
            modif, external_src=f"{voie_id} - rang {rang} - {label}"
        ),
        magie=is_magic,
        action=action,
        attaque=attaque,
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
        raise ValueError(f"Section inconnue '{sub_set}'. Attendu: {list(sections)}")
    section_data = section_data = data.get(sub_set, {})
    cls_ = sections[sub_set]
    out: Dict[str, Any] = {}
    for name, props in section_data.items():
        props = dict(props)
        props["ref"] = name
        out[name] = cls_(**props)
    return out
