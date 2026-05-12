from co.perso_creation import Ressource
from co.perso_data import Peuple, Famille, Profil
from test.test_perso import FakeCarac, FakePersonnage

p = FakePersonnage(
    Peuple.HALFELIN, Famille.COMBATTANT, niveau=1, caract=FakeCarac()
)

Ressource.from_personnage(p)
