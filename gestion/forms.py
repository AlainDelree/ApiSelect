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
    Visite,
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
