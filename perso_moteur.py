from heapq import nsmallest
from typing import Any, Dict, List, Tuple, Union
from co.perso_data import (
    Peuple,
    Profil,
    Famille,
    PROFILS_PAR_FAMILLE,
    DR_PAR_FAMILLE,
    PV_PAR_FAMILLE,
)
from co import bdd_voies as bdd
from co.perso_creation import Personnage, Modificateur, Carac, Modificateurs


def choisir_peuple_par_numero() -> Peuple:
    # Crée une liste stable des valeurs d'Enum (pour l'indexation)
    peuples = list(Peuple)
    while True:
        print("Choisis un peuple :")
        for i, p in enumerate(peuples, start=1):
            print(f"  {i}. {p.value}")
        choix = input("Entre le numéro correspondant : ").strip()

        idx = int(choix)
        if 1 <= idx <= len(peuples):
            selection = peuples[idx - 1]
            print(f"Tu as choisi : {selection.value}\n")
            return selection
        else:
            print("→ Numéro invalide, recommence.\n")

        return selection


def choisir_famille_par_numero() -> Famille:
    # Crée une liste stable des valeurs d'Enum (pour l'indexation)
    familles = list(Famille)
    while True:
        print("Choisis une Famille :")
        for i, p in enumerate(familles, start=1):
            print(f"  {i}. {p.value}")
        choix = input("Entre le numéro correspondant : ").strip()

        idx = int(choix)
        if 1 <= idx <= len(familles):
            selection = familles[idx - 1]
            print(f"Tu as choisi : {selection.value}\n")
            return selection
        else:
            print("→ Numéro invalide, recommence.\n")

        return choix


def choisir_profil_par_numero(famille=None) -> Profil:
    """
    Affiche un menu numéroté de profils :
      - si `famille` est fourni, ne propose que les profils de cette famille ;
      - sinon, propose tous les profils.
    Retourne le Profil choisi.
    """
    # 1) Construire la liste des profils à afficher
    if famille is None:
        profils: List[Profil] = list(Profil)
        titre = "Choisis un Profil"
    else:
        profils_tuple = PROFILS_PAR_FAMILLE.get(famille, ())
        if not profils_tuple:
            print(f"Aucun profil disponible pour la famille « {famille.value} ».")
            profils = list(Profil)
            titre = f"Choisis un Profil (famille « {famille.value} » introuvable → liste complète)"
        else:
            profils = list(profils_tuple)
            titre = f"Choisis un Profil ({famille.value})"

    # 2) Boucle d'input robuste
    while True:
        try:
            print(titre, ":")
            for i, p in enumerate(profils, start=1):
                print(f"  {i}. {p.value}")
            choix = input("Entre le numéro correspondant : ").strip()

            idx = int(choix)
            if 1 <= idx <= len(profils):
                selection = profils[idx - 1]
                print(f"Tu as choisi : {selection.value}\n")
                return selection
            else:
                print("→ Numéro invalide, recommence.\n")
        except KeyboardInterrupt:
            print("\nOpération annulée par l’utilisateur.")
            raise


def choisir_option(
    options: Union[Tuple[str, ...], List[str], Dict[str, Any]],
    return_value_if_dict: bool = False,  # False = retourne la clé ; True = retourne la valeur
) -> str:
    """
    Affiche les options sous forme de liste numérotée et renvoie la valeur choisie.
    - Si options est un tuple/list de strings, retourne la string choisie.
    - Si options est un dict {clé: valeur}, affiche "clé: valeur" et
      retourne la clé (par défaut) ou la valeur si return_value_if_dict=True.
    """

    # Prépare la liste d'affichage et le mapping index -> (clé, valeur)
    items: List[tuple[str, Any]] = []
    if isinstance(options, dict):
        # On garde l'ordre d'insertion (comportement Python 3.7+)
        items = list(options.items())  # [(clé, valeur), ...]
        to_display = [f"{k}: {v}" for k, v in items]
    else:
        # tuple/list
        opts_list = list(options)
        items = [(s, s) for s in opts_list]  # clé=valeur=la même string
        to_display = opts_list

    # Affichage numéroté
    for i, opt in enumerate(to_display, start=1):
        print(f"  {i}. {opt}")

    # Lecture/validation
    n = len(items)
    while True:
        choix = input("> Entrez un numéro : ").strip()
        if choix.isdigit():
            idx = int(choix)
            if 1 <= idx <= n:
                key, value = items[idx - 1]
                print(f"tu as choisi {value}")
                return (
                    value
                    if (isinstance(options, dict) and return_value_if_dict)
                    else key
                )

        print(f"Saisie invalide. Choisissez un numéro entre 1 et {n}.")


def classer_par_selection(
    options: Tuple[str, ...],
    prompt: str = "Choisis la meilleure (numéro) parmi les restantes",
) -> List[str]:
    restantes = list(options)
    classement = []
    tour = 1
    while restantes:
        print(f"\nTour {tour} — éléments restants :")
        for i, opt in enumerate(restantes, start=1):
            print(f"  {i}. {opt}")
        raw = input(f"> {prompt}: ").strip()
        if not raw.isdigit():
            print("Veuillez entrer un numéro.")
            continue
        idx = int(raw)
        if not (1 <= idx <= len(restantes)):
            print("Numéro hors plage.")
            continue
        choix = restantes.pop(idx - 1)
        classement.append(choix)
        tour += 1
    return classement


# donnees
carac_base = {
    "Polyvalent": (2, 2, 2, 1, 1, 0, -1),
    "Expert": (3, 2, 1, 1, 0, 0, -1),
    "Spécialiste": (4, 2, 1, 0, 0, -1, -1),
}


bonus_peuples = {
    "Demi-Elfe": {"bonus": ["PER", "CHAR"], "malus": ["FOR", "CON"]},
    "Demi-orc": {"bonus": ["FOR", "CON"], "malus": ["CHAR", "INT"]},
    "Elfe Haut": {"bonus": ["INT", "CHAR"], "malus": ["FOR"]},
    "Elfe Sylvain": {"bonus": ["AGI", "PER"], "malus": ["FOR"]},
    "Gnome": {"bonus": ["INT", "PER"], "malus": ["FOR"]},
    "Halfelin": {"bonus": ["AGI", "VOL"], "malus": ["FOR"]},
    "Nain": {"bonus": ["CON", "VOL"], "malus": ["AGI"]},
}

profils_type = {
    "Arquebusier": {"AGI", "INT", "CON", "PER", "VOL", "FOR", "CHAR"},
    "Barde": {"CHAR", "AGI", "VOL", "PER", "INT", "FOR", "CON"},
    "Rôdeur": {"AGI", "PER", "CON", "FOR", "INT", "VOL", "CHAR"},
    "Barbare": {"FOR", "CON", "AGI", "PER", "INT", "INT", "CHAR"},
    "Chevalier": {"FOR", "CHAR", "CON", "VOL", "INT", "INT", "PER"},
    "Guerrier": {"FOR", "CON", "AGI", "PER", "VOL", "INT", "CHAR"},
    "Ensorceleur": {"CHAR", "VOL", "AGI", "INT", "PER", "CON", "FOR"},
    "Forgesort": {"INT", "VOL", "CON", "AGI", "PER", "CHAR", "FOR"},
    "Magicien": {"INT", "VOL", "AGI", "CHAR", "PER", "FOR", "CON"},
    "Sorcier": {"INT", "VOL", "CON", "CHAR", "FOR", "PER", "AGI"},
    "Druide": {"PER", "VOL", "CON", "AGI", "CHAR", "INT", "FOR"},
    "Moine": {"VOL", "PER", "AGI", "FOR", "CON", "CHAR", "INT"},
    "Prêtre": {"CHAR", "VOL", "FOR", "CON", "INT", "PER", "AGI"},
}

modifs_profils = {"Aventurier": Modificateur(label="PC", val=1, source="Aventurier")}


# 1. peuples


def main():

    name = "Choisis un Nom"

    print("Choisis un Peuple", flush=True)
    peuple = choisir_peuple_par_numero()
    print("Choisis une famille de profils", flush=True)
    famille = choisir_famille_par_numero()
    print("Choisis uun Profil", flush=True)
    profil = choisir_profil_par_numero(famille=famille)

    print("________________________")
    print("Choisis ton Profil statistique", flush=True)
    profil_stat = choisir_option(carac_base)
    print("Classe tes carac", flush=True)
    print(
        f"veux tu utiliser un profil type de {profil.value}  : {profils_type[profil.value]} ?"
    )

    choix = choisir_option(["Oui", "Non"])
    if choix == "Oui":
        carac_ordre = profils_type[profil.value]
    else:
        carac_ordre = classer_par_selection(
            (("FOR", "INT", "VOL", "CON", "AGI", "PER", "CHA"))
        )

    print("________________________")
    stats_initiales = {s: v for s, v in zip(carac_ordre, carac_base[profil_stat])}
    print("voilà votre profil de base : \n", peuple, stats_initiales)

    bonus_peuples["Humain"] = {
        "bonus": list(nsmallest(2, stats_initiales, key=stats_initiales.get)),
        "malus": [],
    }
    bonus_malus_to_choose = bonus_peuples[peuple.value]
    print("________________________")
    print("votre Peuple vous octroie un bonus et un malus à choisir parmi: ")
    print(
        f"bonus : {bonus_malus_to_choose['bonus']} - 'malus' : {bonus_malus_to_choose['malus']}"
    )

    if len(bonus_malus_to_choose["bonus"]) > 1:
        bonus = choisir_option(bonus_malus_to_choose["bonus"], "choix du bonus +1")
    else:
        bonus = bonus_malus_to_choose["bonus"][0]

    if len(bonus_malus_to_choose["malus"]) > 1:
        malus = choisir_option(bonus_malus_to_choose["malus"], "choix du malus -1")
    else:
        if len(bonus_malus_to_choose["malus"]) > 0:
            malus = bonus_malus_to_choose["malus"][0]
        else:
            malus = ""

    print("Tes modificateurs de peuple sont:")
    print(f"bonus +1 : {bonus} - malus -1 : {malus}")

    perso = Personnage(
        nom=name,
        peuple=peuple,
        famille=famille,
        profil=profil,
        niveau=1,
        caract=Carac.from_dict(stats_initiales),
        mod=Modificateurs(),
    )
    mod_bonus = Modificateur(label=bonus, val=1, source="bonus peuple")
    perso.mod.add(mod_bonus)
    if malus != "":
        mod_malus = Modificateur(label=malus, val=-1, source="malus peuple")
        perso.mod(mod_malus)
    perso.rollup_mod = perso.compute_rollup_modif()

    print(perso)


if __name__ == "__main__":
    main()
