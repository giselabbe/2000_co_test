from importlib import reload
import co.perso_creation as perso

reload(perso)

ARMES = perso.load_materiel("data/lst_equipement.yml", sub_set="ARMES")
ARMURES = perso.load_materiel("data/lst_equipement.yml", sub_set="ARMURES")


# ========== LHAGVA ==========

lhagva = perso.Personnage(
    nom="Lhagva",
    peuple=perso.Peuple.HUMAIN,
    famille=perso.Famille.COMBATTANT,
    profil=perso.Profil.BARBARE,
    niveau=1,
    caract=perso.Carac(AGI=1, CONST=2, FOR=3, PER=1, CHAR=-1, INT=0, VOL=1),
)

lhagva.ressources = perso.Ressource(
    DEF=16, INIT=14, PV=16, PC=2, DR=(4, 10), PM=0, ATK=4, ATD=2, ATM=2
)

lhagva.ajouter_arme(ARMES["EPEE_COURBE"])
lhagva.ajouter_arme(ARMES["JAVELOT"])
lhagva.ajouter_armure(ARMURES["VESTE_CUIR"])

# ========== SKODJA ==========

skodja = perso.Personnage(
    nom="Skodja",
    peuple=perso.Peuple.DEMI_ORC,
    famille=perso.Famille.MYSTIQUE,
    profil=perso.Profil.DRUIDE,
    niveau=1,
    caract=perso.Carac(AGI=2, CONST=1, FOR=2, PER=2, CHAR=-1, INT=-1, VOL=2),
)


skodja.ressources = perso.Ressource(
    DEF=15, INIT=15, PV=9, PC=1, DR=(4, 8), PM=3, ATK=3, ATD=3, ATM=3
)

skodja.ajouter_arme(ARMES["PIQUE"])
skodja.ajouter_arme(ARMES["ARC_COURT"])
skodja.ajouter_armure(ARMURES["VESTE_TISSUS"])

skodja.mod
skodja.rollup_mod

# ========== WILIBERT ==========

wilibert = perso.Personnage(
    nom="Wilibert",
    peuple=perso.Peuple.GNOME,
    famille=perso.Famille.AVENTURIER,
    profil=perso.Profil.VOLEUR,
    niveau=1,
    caract=perso.Carac(AGI=2, CONST=1, FOR=0, PER=2, CHAR=2, INT=0, VOL=0),
)
wilibert.ressources = perso.Ressource(
    DEF=14, INIT=12, PV=9, PC=5, DR=(3, 8), PM=1, ATK=1, ATD=3, ATM=1
)

wilibert.ajouter_arme(ARMES["EPEE_COURTE"])
wilibert.ajouter_arme(ARMES["COUTEAU"])
wilibert.ajouter_armure(ARMURES["VESTE_CUIR"])


# ========== IONAS ==========
reload(perso)

ionas = perso.Personnage(
    nom="Ionas",
    peuple=perso.Peuple.ELFE_HAUT,
    famille=perso.Famille.MAGE,
    profil=perso.Profil.ENSORCELEUR,
    niveau=1,
    caract=perso.Carac(AGI=1, CONST=1, FOR=-2, PER=0, CHAR=4, INT=0, VOL=2),
)
ionas.ressources = perso.Ressource(
    DEF=12, INIT=11, PV=7, PC=6, DR=(3, 6), PM=5, ATK=-1, ATD=2, ATM=3
)

ionas.ajouter_arme(ARMES["BATON_FERRE"])
ionas.apprendre_sort(SPELLBOOK["MURMURE_DANS_LE_VENT"])

ionas.equipement.spellbook
ionas.rollup_mod
ionas.to_dict()


[s.label for s in ionas.equipement.spellbook.values()]
