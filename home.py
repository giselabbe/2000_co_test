import streamlit as st
import json

from co.perso_data import Peuple, Famille, Profil, PROFILS_PAR_FAMILLE
from co.perso_creation import (
    Personnage,
    Carac,
    Arme,
    Armure,
    Equipement,
    Capacite,
    Capacites,
    Ressource,
    Modificateur,
    Modificateurs,
    load_materiel,
)

# --- Catalogue
ARMES = load_materiel("data/lst_equipement.yml", sub_set="ARMES")
ARMURES = load_materiel("data/lst_equipement.yml", sub_set="ARMURES")

st.set_page_config(page_title="Créateur de Personnage JdR", layout="wide")
st.title("Créateur de Personnage COF2")


# --- Helper: sélecteur d'enum qui renvoie directement le membre Enum
def enum_select(
    label,
    enum_cls,
    *,
    key=None,
    on_change=None,
    disabled=False,
    placeholder=None,
    index=None,
):
    """
    Sélecteur d'Enum homogène:
    - options = liste des membres Enum (ex: [Famille.AVENTURIER, Famille.MAGE, ...])
    - format_func = affiche e.value si présent, sinon str(e)
    - renvoie le membre Enum sélectionné
    - si `key` est fourni, st.session_state[key] contiendra le membre Enum
    - `index=None` + `placeholder` affiche le placeholder tant qu'aucun choix n'est fait (Streamlit >= 1.31)
    """
    return st.selectbox(
        label,
        options=list(enum_cls),
        format_func=lambda e: e.value if hasattr(e, "value") else str(e),
        key=key,
        on_change=on_change,
        disabled=disabled,
        placeholder=placeholder,
        index=index,
    )


# --- Session keys init (valeurs par défaut)
for key in ("nom", "peuple", "famille", "profil"):
    st.session_state.setdefault(key, None)


def on_famille_change():
    """Quand la famille change, on remet le profil à None pour forcer un nouveau choix."""
    st.session_state["profil"] = None


# --- Identité
st.subheader("Identité")
col1, col2, col3, col4 = st.columns(4)

with col1:
    nom = st.text_input("Nom", value=st.session_state["nom"] or "Lhagva", key="nom")

with col2:
    # ⚠️ Si Streamlit < 1.31, retire index=None et placeholder
    peuple = enum_select(
        "Peuple",
        Peuple,
        key="peuple",
        placeholder="Choisissez un Peuple",
        index=None,
    )

with col3:
    famille = enum_select(
        "Famille",
        Famille,
        key="famille",
        on_change=on_famille_change,
        placeholder="Choisissez une Famille",
        index=None,
    )

with col4:
    # Profils disponibles selon la famille (membre Enum ou None)
    profils_disponibles = list(PROFILS_PAR_FAMILLE.get(st.session_state["famille"], ()))

    # Calcul d'index par défaut si un profil était en session et reste valide
    if st.session_state["profil"] in profils_disponibles:
        default_index = profils_disponibles.index(st.session_state["profil"])
    else:
        default_index = None  # affiche le placeholder si supporté

    profil = st.selectbox(
        "Profil",
        options=profils_disponibles,
        format_func=lambda p: p.value,
        key="profil",
        index=default_index,
        disabled=(len(profils_disponibles) == 0),
        placeholder="Choisissez d’abord une Famille",
    )

niveau = st.number_input("Niveau", min_value=1, max_value=20, value=1, step=1)

# --- Équipement (persistance dans la session)
st.subheader("Équipement")
if "equipement" not in st.session_state:
    st.session_state["equipement"] = Equipement()
equipement = st.session_state["equipement"]


# --- Helpers
def norm_lower(v):
    return v.strip().lower() if isinstance(v, str) else v


def render_catalog_readonly(catalog_dict: dict, title_singular: str, key_prefix: str):
    """
    - catalog_dict: Dict[str, objet] avec une méthode .to_dict()
    - title_singular: 'Arme' | 'Armure' (pour les libellés)
    - key_prefix: 'arme' | 'armure' (pour les keys Streamlit)

    Retourne:
    - ref_sel: la référence sélectionnée (str ou None)
    - data: dict des caractéristiques (lecture seule) ou None
    - obj: l'objet sélectionné (pour un éventuel ajout)
    """
    refs = sorted(catalog_dict.keys())
    ref_sel = st.selectbox(
        f"Référence {title_singular.lower()}",
        options=refs,
        format_func=lambda r: (
            f"{r} — {getattr(catalog_dict.get(r), 'label', '')}"
            if r in catalog_dict
            else str(r)
        ),
        placeholder=f"Choisissez une {title_singular.lower()}...",
        key=f"{key_prefix}_ref_select",
        index=None,  # ⚠️ retire si Streamlit < 1.31
    )

    if not ref_sel:
        return None, None, None

    obj = catalog_dict[ref_sel]
    data = obj.to_dict()  # doit contenir au minimum: ref, label

    # Normalisations éventuelles (armes)
    if title_singular.lower() == "arme":
        data["type_attaque"] = norm_lower(data.get("type_attaque", "contact"))
        data["type_degat"] = norm_lower(data.get("type_degat", "tranchant"))

    # Affichage lecture seule
    st.markdown("#### Caractéristiques (lecture seule)")
    col1, col2, col3 = st.columns([1.2, 1.0, 1.0])

    with col1:
        st.text(f"Réf. : {data.get('ref', ref_sel)}")
        st.text(f"Label : {data.get('label', ref_sel)}")
        # Champs communs possibles
        if "DM" in data:
            st.text(f"DM : {data.get('DM', '—')}")

    with col2:
        if "type_attaque" in data:
            st.text(f"Type d'attaque : {data.get('type_attaque', '—')}")
        if "type_degat" in data:
            st.text(f"Type de dégât : {data.get('type_degat', '—')}")

    with col3:
        if "portee" in data:
            st.text(f"Portée : {data.get('portee', 0)}")
        if "prix" in data:
            st.text(f"Prix : {data.get('prix', -1)}")
        if data.get("obs"):
            st.text(f"Observations : {data.get('obs')}")

    return ref_sel, data, obj


def fmt_def(modif_obj) -> str:
    """Affiche le modificateur DEF sous forme 'DEF: +2' ou '—' si absent."""
    if not modif_obj:
        return "—"
    # Objet Modificateur
    if hasattr(modif_obj, "label") and hasattr(modif_obj, "val"):
        signe = "+" if modif_obj.val >= 0 else ""
        return f"{modif_obj.label}: {signe}{modif_obj.val}"
    # Dict (via to_dict)
    if isinstance(modif_obj, dict):
        label = modif_obj.get("label", "DEF")
        val = modif_obj.get("val", 0)
        signe = "+" if val >= 0 else ""
        return f"{label}: {signe}{val}"
    return "—"


# --- Armes
with st.expander("Armes", expanded=True):
    ref_sel, data, arme_obj = render_catalog_readonly(ARMES, "Arme", "arme")

    if ref_sel and data:
        # Anti-doublon
        already = ref_sel in getattr(equipement, "armes", {})
        if st.button(
            "➜ Ajouter cette arme à l'équipement",
            key=f"add_arme_{ref_sel}",
            disabled=already,
        ):
            try:
                # Recréer une instance (copie indépendante)
                equipement.armes[ref_sel] = Arme(
                    ref=data.get("ref", ref_sel),
                    label=data.get("label"),
                    DM=data.get("DM"),
                    type_attaque=data.get("type_attaque"),
                    type_degat=data.get("type_degat"),
                    prix=data.get("prix", -1),
                    portee=data.get("portee", 0),
                    obs=data.get("obs", ""),
                )
                st.session_state["equipement"] = equipement
                st.success(
                    f"Arme « {data.get('label', ref_sel)} » ajoutée (ref: {ref_sel})."
                )
            except Exception as e:
                st.error(f"Impossible d'ajouter l'arme : {e}")

        if already:
            st.info("Cette arme est déjà présente dans l'équipement.")

# --- Armures
with st.expander("Armures", expanded=True):
    refs_armures = sorted(ARMURES.keys())
    ref_arm = st.selectbox(
        "Référence armure",
        options=refs_armures,
        format_func=lambda r: (
            f"{r} — {getattr(ARMURES.get(r), 'label', '')}" if r in ARMURES else str(r)
        ),
        index=None,  # ⚠️ retire si Streamlit < 1.31
        placeholder="Choisissez une armure...",
        key="armure_ref_select",
    )

    if ref_arm:
        armure_obj = ARMURES[ref_arm]
        d = (
            armure_obj.to_dict()
        )  # attendu: ref, label, prix, modif={'label','val'}, obs (optionnel)

        ref_val = d.get("ref", ref_arm)
        label_val = d.get("label", ref_arm)
        prix_val = d.get("prix", -1)
        modif_val = d.get("modif", {})  # ex {'label': 'DEF', 'val': 2}
        obs_val = d.get("obs", "")

        st.markdown("#### Caractéristiques (lecture seule)")
        col1, col2 = st.columns([1.2, 1.2])

        with col1:
            st.text(f"Réf. : {ref_val}")
            st.text(f"Label : {label_val}")
            st.text(f"Prix : {prix_val}")

        with col2:
            st.text(
                f"Modificateur : {fmt_def(armure_obj.modif)}"
            )  # <- objet Modificateur
            if obs_val:
                st.text(f"Observations : {obs_val}")

        # Ajout + anti-doublon
        already_armure = ref_arm in getattr(equipement, "armures", {})
        if st.button(
            "➜ Ajouter cette armure à l'équipement",
            key=f"add_armure_{ref_arm}",
            disabled=already_armure,
        ):
            try:
                equipement.armures[ref_arm] = Armure(
                    ref=ref_val,
                    label=label_val,
                    prix=prix_val,
                    modif=armure_obj.modif,  # garder l'objet Modificateur tel quel
                    obs=obs_val,
                )
                st.session_state["equipement"] = equipement
                st.success(f"Armure « {label_val} » ajoutée (ref: {ref_arm}).")
            except Exception as e:
                st.error(f"Impossible d'ajouter l'armure : {e}")

        if already_armure:
            st.info("Cette armure est déjà présente dans l'équipement.")


"""
        # 4) Ajout au modèle d'équipement
        if st.button("➕ Ajouter l'arme", key=f"add_{ref_sel}"):
            try:
                equipement.armes[ref_sel] = Arme(
                    ref=ref_sel,
                    label=label_a,
                    DM=DM,
                    type_attaque=type_attaque,
                    type_degat=type_degat,
                    prix=prix_a,
                    portee=portee,
                    obs=obs_a,
                )
                st.success(f"Arme « {label_a} » ajoutée (ref: {ref_sel}).")
            except Exception as e:
                st.error(f"Impossible d'ajouter l'arme : {e}")

    # 5) (Optionnel) Afficher un récap des armes déjà ajoutées cette session
    if getattr(equipement, "armes", None):
        st.markdown("### Armes ajoutées")
        for ref, a in equipement.armes.items():
            st.write(
                f"- **{a.label}** *(ref: {ref})* — DM : {a.DM}, type attaque : {a.type_attaque}, "
                f"type dégât : {a.type_degat}, portée : {a.portee}, prix : {a.prix}. {a.obs or ''}"
            )

with st.expander("Armures"):
ref_r = st.text_input("Réf. Armure", "VESTE_CUIR")
label_r = st.text_input("Label Armure", "Veste en Cuir Simple")
prix_r = st.number_input("Prix armure", value=4)
mod_label = st.selectbox(
"Mod label", ["DEF", "INIT", "PC", "ATK", "ATD", "ATM"]
)
mod_val = st.number_input("Mod valeur", value=2)
obs_r = st.text_input("Observations Armure", "")
if st.button("➕ Ajouter l'armure"):
equipement.armures[ref_r] = Armure(
ref=ref_r,
label=label_r,
prix=prix_r,
modif={"label": mod_label, "val": mod_val},
obs=obs_r,
)
st.success(f"Armure {label_r} ajoutée.")

with st.expander("Sac"):
item = st.text_input("Objet")
qty = st.number_input("Quantité", value=1, step=1)
if st.button("➕ Ajouter au sac"):
equipement.sac[item] = qty
st.success(f"{item} x{qty} ajouté au sac.")

st.subheader("Capacités")
capacites = Capacites()
with st.expander("Ajouter une capacité"):
cap_key = st.text_input("Clé (ex: HUMAIN)")
cap_ref = st.text_input("Réf.", "HUMAIN")
cap_label = st.text_input("Label", "Diversité")
cap_rang = st.number_input("Rang", value=1, step=1)
cap_desc = st.text_area("Description", "…")
cap_mod_k = st.text_input("Mod clé (ex: PC)")
cap_mod_v = st.number_input("Mod valeur", value=1)
if st.button("➕ Ajouter la capacité"):
cap = Capacite(
ref=cap_ref,
label=cap_label,
rang=cap_rang,
description=cap_desc,
modif=({cap_mod_k: cap_mod_v} if cap_mod_k else {}),
)
if cap_key:
capacites.list_of_skills[cap_key] = cap
st.success(f"Capacité {cap_label} ajoutée sous clé {cap_key}.")

st.subheader("Ressources")
r1, r2, r3, r4, r5, r6, r7, r8, r9 = st.columns(9)
with r1:
PV = st.number_input("PV", value=12)
with r2:
DR_min = st.number_input("DR min", value=4)
with r3:
DR_max = st.number_input("DR max", value=10)
with r4:
PM = st.number_input("PM", value=1)
with r5:
PC = st.number_input("PC", value=2)
with r6:
INIT = st.number_input("INIT", value=11)
with r7:
DEF = st.number_input("DEF", value=11)
with r8:
ATK = st.number_input("ATK", value=3)
with r9:
ATD = st.number_input("ATD", value=2)
ATM = st.number_input("ATM", value=2)
ressources = Ressource(
PV=PV,
DR=(int(DR_min), int(DR_max)),
PM=PM,
PC=PC,
INIT=INIT,
DEF=DEF,
ATK=ATK,
ATD=ATD,
ATM=ATM,
)

st.subheader("Modificateurs")
mods = Modificateurs()
with st.expander("Ajouter un mod"):
m_label = st.selectbox("Label", ["DEF", "INIT", "PC", "ATK", "ATD", "ATM"])
m_val = st.number_input("Valeur", value=1)
m_source = st.text_input("Source", "VOIE_DU_POURFENDEUR")
m_comment = st.text_input("Commentaire", "")
if st.button("➕ Ajouter le mod"):
mods.liste_mods.append(
Modificateur(
    label=m_label, val=int(m_val), source=m_source, comment=m_comment
)
)
st.success(f"Mod {m_label} +{m_val} ajouté ({m_source}).")
rollup_mod = mods.rollup() if hasattr(mods, "rollup") else {}

st.subheader("Aperçu")
personnage = Personnage(
nom=nom,
peuple=peuple,
famille=famille,
profil=profil,
niveau=niveau,
caract=carac,
equipement=equipement,
voies={},
capacites=capacites,
spells=Capacites(),
ressources=ressources,
mod=mods,
rollup_mod=rollup_mod,
)
st.json(personnage.to_dict())

cjson, cyaml = st.columns(2)
with cjson:
if st.button("💾 Enregistrer JSON"):
from pathlib import Path

path = Path(f"{nom}.json")
with path.open("w", encoding="utf-8") as f:
json.dump(personnage.to_dict(), f, indent=2, ensure_ascii=False)
st.success(f"Fichier JSON enregistré: {path}")
"""
