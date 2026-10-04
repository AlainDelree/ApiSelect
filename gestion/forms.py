"""Formulaire de saisie de visite (issue #43), à grands boutons à
toucher : un choix par groupe pour les champs simples (observation de
la reine, réserves, comportement), plusieurs choix possibles pour les
actions et pour chaque observation.

Pour chaque observation (essaimage, reine morte, pillage, frelons),
le champ est un groupe de trois boutons « Non / Constaté / Doute » :
un seul choix pour couvrir à la fois « cette observation a eu lieu »
et sa certitude.
"""

from django import forms

from .models import (
    CertitudeObservation,
    Comportement,
    NiveauReserves,
    ObservationReine,
    ReponseCellulesRoyales,
    TypeActionVisite,
    TypeObservationVisite,
    Visite,
    date_revisite_par_defaut,
)

CHOIX_PRESENCE_OBSERVATION = [
    ("", "Non"),
    (CertitudeObservation.CONSTATE, "Constaté"),
    (CertitudeObservation.DOUTE, "Doute"),
]

CHOIX_OUI_NON = [("oui", "Oui"), ("non", "Non")]


class VisiteForm(forms.ModelForm):
    actions = forms.MultipleChoiceField(
        label="Actions faites pendant la visite",
        choices=TypeActionVisite.choices, required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "groupe-choix"}),
    )
    observation_essaimage = forms.ChoiceField(
        label="Colonie essaimée",
        choices=CHOIX_PRESENCE_OBSERVATION, required=False,
        widget=forms.RadioSelect(attrs={"class": "groupe-choix"}),
    )
    reponse_cellules_royales = forms.ChoiceField(
        label="Si essaimage : cellules royales",
        choices=ReponseCellulesRoyales.choices, required=False,
        widget=forms.RadioSelect(attrs={"class": "groupe-choix"}),
    )
    observation_reine_morte = forms.ChoiceField(
        label="Reine morte",
        choices=CHOIX_PRESENCE_OBSERVATION, required=False,
        widget=forms.RadioSelect(attrs={"class": "groupe-choix"}),
    )
    date_reverification_reine_morte = forms.DateField(
        label="Si doute sur la reine morte : revérifier le",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    observation_pillage = forms.ChoiceField(
        label="Pillage",
        choices=CHOIX_PRESENCE_OBSERVATION, required=False,
        widget=forms.RadioSelect(attrs={"class": "groupe-choix"}),
    )
    observation_frelons = forms.ChoiceField(
        label="Frelons",
        choices=CHOIX_PRESENCE_OBSERVATION, required=False,
        widget=forms.RadioSelect(attrs={"class": "groupe-choix"}),
    )

    class Meta:
        model = Visite
        fields = [
            "date", "observation_reine", "nb_cadres_couvain",
            "nb_cadres_abeilles", "reserves", "comportement", "notes",
        ]
        labels = {
            "date": "Date de la visite",
            "observation_reine": "Observation de la reine",
            "nb_cadres_couvain": "Cadres de couvain",
            "nb_cadres_abeilles": "Cadres d'abeilles",
            "reserves": "Réserves",
            "comportement": "Comportement",
            "notes": "Notes",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "observation_reine": forms.RadioSelect(attrs={"class": "groupe-choix"}),
            "reserves": forms.RadioSelect(attrs={"class": "groupe-choix"}),
            "comportement": forms.RadioSelect(attrs={"class": "groupe-choix"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_visite = cleaned_data.get("date")
        date_reverification = cleaned_data.get("date_reverification_reine_morte")
        if date_visite and date_reverification and date_reverification < date_visite:
            self.add_error(
                "date_reverification_reine_morte",
                "La date de revérification ne peut pas être antérieure "
                "à la date de la visite.",
            )
        return cleaned_data


def initial_observations_depuis_visite(visite):
    """Valeurs initiales des champs d'observation, d'action et de
    revérification du formulaire à boutons, à partir de ce qui est déjà
    enregistré pour cette visite — utilisé pour pré-remplir le même
    formulaire en modification (issue #48). Sans rappel existant, la
    date de revérification proposée reste calculée de la même façon
    qu'à la création, mais à partir de la date de la visite plutôt que
    d'aujourd'hui."""
    observations = {obs.type_observation: obs for obs in visite.observations.all()}
    essaimage = observations.get(TypeObservationVisite.ESSAIMAGE)
    reine_morte = observations.get(TypeObservationVisite.REINE_MORTE)
    pillage = observations.get(TypeObservationVisite.PILLAGE)
    frelons = observations.get(TypeObservationVisite.FRELONS)
    rappel = getattr(reine_morte, "rappel", None) if reine_morte else None
    return {
        "actions": list(visite.actions.values_list("type_action", flat=True)),
        "observation_essaimage": essaimage.certitude if essaimage else "",
        "reponse_cellules_royales": essaimage.reponse_cellules_royales if essaimage else "",
        "observation_reine_morte": reine_morte.certitude if reine_morte else "",
        "date_reverification_reine_morte": (
            rappel.date_revisite if rappel else date_revisite_par_defaut(visite.date)
        ),
        "observation_pillage": pillage.certitude if pillage else "",
        "observation_frelons": frelons.certitude if frelons else "",
    }


class RevisiteReineMorteForm(forms.Form):
    """Posée au passage suivant quand une observation « reine morte »
    reste ouverte : couvain ouvert (œufs ou jeunes larves) présent ?
    Oui → infirmée, non → confirmée."""

    couvain_ouvert_present = forms.TypedChoiceField(
        label="Couvain ouvert présent ?",
        choices=CHOIX_OUI_NON,
        coerce=lambda valeur: valeur == "oui",
        widget=forms.RadioSelect(attrs={"class": "groupe-choix"}),
    )
