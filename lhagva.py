import co.perso_creation as perso
from co import bdd_voies as bdd
from co import io_helpers as io

bdd_path = bdd.DB_PATH
ARMES = perso.load_materiel("data/lst_equipement.yml", sub_set="ARMES")
ARMURES = perso.load_materiel(
    "data/lst_equipement.yml", sub_set="ARMURES"
)


lhagva = perso.Personnage(
    nom="Lhagva",
    peuple=perso.Peuple.HUMAIN,
    famille=perso.Famille.COMBATTANT,
    profil=perso.Profil.BARBARE,
    niveau=1,
    caract=perso.Carac(
        AGI=1, CONST=2, FOR=3, PER=1, CHAR=-1, INT=0, VOL=1
    ),
)

lh_arme = ARMES["EPEE_COURBE"]
lh_armure = ARMURES["VESTE_CUIR"]

lhagva.ajouter_arme(lh_arme)
lhagva.ajouter_armure(lh_armure)

sk1 = perso.ppl_skill_from_bdd(
    bdd_path, lhagva.peuple.name, voie_rang=1
)
sk2 = perso.classe_skill_from_bdd(
    bdd_path, "VOIE_DE_LA_RAGE", voie_rang=1
)
sk3 = perso.classe_skill_from_bdd(
    bdd_path, "VOIE_DU_POURFENDEUR", voie_rang=1
)

lhagva.ajouter_capacite(sk1)
lhagva.ajouter_capacite(sk2)
lhagva.ajouter_capacite(sk3)
lhagva.compute_rollup_modif()


io.save_yaml(lhagva.to_dict(), "data/lhagva.yml")
