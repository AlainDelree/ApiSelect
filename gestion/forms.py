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
from django.utils import timezone

from selection.models import (
    MODES_ACQUISITION_ACHAT,
    CouleurMarquage,
    ModeAcquisitionReine,
    Reine,
    StatutReine,
)

from .couleurs import couleur_marquage_proposee

from .models import (
    CertitudeObservation,
    Comportement,
    NiveauReserves,
    ObservationReine,
    ReponseCellulesRoyales,
    TypeActionVisite,
    TypeObservationVisite,
    Vendeur,
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


CHOIX_ORIGINE_REINE = [
    ("EXISTANTE", "Reine déjà enregistrée, non affectée"),
    ("NOUVELLE", "Nouvelle reine à créer"),
]


class ReineForm(forms.ModelForm):
    """Formulaire unique pour tous les champs d'une reine (issue #54),
    réutilisé pour la création, la modification (fiche colonie et page
    « Reines ») et le remplacement (`NouvelleReineForm` ci-dessous, qui
    en hérite) : les mêmes champs partout, pour qu'il ne reste plus
    rien qui ne se règle que par l'administration. Pour un achat, le
    vendeur se choisit dans la liste ou se crée directement ici — pas
    de second écran de saisie (issue #51)."""

    mere = forms.ModelChoiceField(
        label="Mère (si connue)", queryset=Reine.objects.all(), required=False,
    )
    vendeur = forms.ModelChoiceField(
        label="Vendeur déjà enregistré", queryset=Vendeur.objects.all(), required=False,
    )
    nouveau_vendeur_nom = forms.CharField(
        label="Ou nouveau vendeur — nom", max_length=150, required=False,
    )
    nouveau_vendeur_telephone = forms.CharField(
        label="Téléphone du vendeur", max_length=30, required=False,
    )
    nouveau_vendeur_adresse = forms.CharField(
        label="Adresse du vendeur", max_length=255, required=False,
    )
    marquage_effectue = forms.TypedChoiceField(
        label="Marquage effectué",
        choices=CHOIX_OUI_NON, coerce=lambda valeur: valeur == "oui",
        initial="non",
        widget=forms.RadioSelect(attrs={"class": "groupe-choix"}),
    )
    couleur_marquage = forms.ChoiceField(
        label="Couleur du marquage",
        choices=[("", "—")] + list(CouleurMarquage.choices), required=False,
    )

    class Meta:
        model = Reine
        fields = [
            "identifiant", "mere", "statut", "mode_acquisition", "vendeur",
            "date_naissance", "date_fecondation", "station_fecondation",
            "marquage_effectue", "date_marquage", "couleur_marquage",
            "date_deces", "lignee_male_probable", "notes",
        ]
        labels = {
            "identifiant": "Identifiant",
            "statut": "Statut",
            "mode_acquisition": "Mode d'acquisition",
            "date_naissance": "Date de naissance",
            "date_fecondation": "Date de fécondation",
            "station_fecondation": "Station de fécondation",
            "date_marquage": "Date de marquage",
            "date_deces": "Date de décès",
            "lignee_male_probable": "Lignée mâle probable",
            "notes": "Notes",
        }
        widgets = {
            "statut": forms.RadioSelect(attrs={"class": "groupe-choix"}),
            "mode_acquisition": forms.RadioSelect(attrs={"class": "groupe-choix"}),
            "date_naissance": forms.DateInput(attrs={"type": "date"}),
            "date_fecondation": forms.DateInput(attrs={"type": "date"}),
            "date_marquage": forms.DateInput(attrs={"type": "date"}),
            "date_deces": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["statut"].required = False
        self.fields["statut"].choices = [("", "Non renseigné")] + list(StatutReine.choices)
        self.fields["mode_acquisition"].required = False
        self.fields["mode_acquisition"].choices = (
            [("", "Non renseigné")] + list(ModeAcquisitionReine.choices)
        )
        # Valeur à restaurer si le marquage n'est pas (ou plus) effectué à
        # l'enregistrement : une couleur déjà enregistrée en base n'est
        # jamais effacée silencieusement par une simple modification (cf.
        # `save`) ; capturée ici, avant que `construct_instance` ne mette
        # à jour `self.instance` avec les données du formulaire.
        self._couleur_marquage_avant = (
            self.instance.couleur_marquage if self.instance.pk else ""
        )
        if self.instance.pk and not self.is_bound:
            couleur_proposee = couleur_marquage_proposee(self.instance)
            if couleur_proposee:
                self.fields["couleur_marquage"].initial = couleur_proposee

    def clean_identifiant(self):
        identifiant = self.cleaned_data.get("identifiant", "")
        if not identifiant:
            return identifiant
        queryset = Reine.objects.filter(identifiant=identifiant)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(
                "Cet identifiant est déjà utilisé par une autre reine.",
            )
        return identifiant

    def _date_marquage_par_defaut(self, cleaned_data):
        return timezone.localdate()

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("mode_acquisition") in MODES_ACQUISITION_ACHAT
            and not cleaned_data.get("vendeur")
            and not cleaned_data.get("nouveau_vendeur_nom")
        ):
            self.add_error(
                "vendeur", "Choisissez un vendeur ou renseignez-en un nouveau.",
            )
        if cleaned_data.get("marquage_effectue"):
            if not cleaned_data.get("date_marquage"):
                cleaned_data["date_marquage"] = self._date_marquage_par_defaut(cleaned_data)
            if not cleaned_data.get("couleur_marquage"):
                self.add_error(
                    "couleur_marquage",
                    "La couleur du marquage est obligatoire si le marquage "
                    "est effectué.",
                )
        return cleaned_data

    def save(self, commit=True):
        reine = super().save(commit=False)
        vendeur = self.cleaned_data.get("vendeur")
        if vendeur is None and self.cleaned_data.get("nouveau_vendeur_nom"):
            vendeur = Vendeur.objects.create(
                nom=self.cleaned_data["nouveau_vendeur_nom"],
                telephone=self.cleaned_data.get("nouveau_vendeur_telephone", ""),
                adresse=self.cleaned_data.get("nouveau_vendeur_adresse", ""),
            )
        reine.vendeur = vendeur
        if not reine.marquage_effectue:
            reine.couleur_marquage = (
                self.cleaned_data.get("couleur_marquage") or self._couleur_marquage_avant
            )
        if commit:
            reine.save()
        return reine


class NouvelleReineForm(ReineForm):
    """Formulaire de remplacement de reine depuis la fiche colonie
    (issue #51), à grands boutons comme le formulaire de visite. En
    plus des champs de la reine (communs avec la création et la
    modification, issue #54, hérités de `ReineForm`) : la date de
    remplacement et le choix entre une reine déjà enregistrée et non
    affectée à une colonie active (ex. issue d'une cellule royale
    devenue reine), ou une nouvelle reine créée dans la foulée — ces
    deux derniers champs n'existent que pour un remplacement."""

    date_remplacement = forms.DateField(
        label="Date de remplacement",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    origine = forms.ChoiceField(
        label="Reine",
        choices=CHOIX_ORIGINE_REINE,
        initial="NOUVELLE",
        widget=forms.RadioSelect(attrs={"class": "groupe-choix"}),
    )
    reine_existante = forms.ModelChoiceField(
        label="Reine déjà enregistrée",
        queryset=Reine.objects.all(), required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["identifiant"].required = False
        self.fields["reine_existante"].queryset = (
            Reine.objects.exclude(colonie_dirigee__active=True).distinct()
        )

    def _date_marquage_par_defaut(self, cleaned_data):
        return cleaned_data.get("date_remplacement") or timezone.localdate()

    def clean(self):
        cleaned_data = super().clean()
        origine = cleaned_data.get("origine")
        if origine == "EXISTANTE":
            if not cleaned_data.get("reine_existante"):
                self.add_error(
                    "reine_existante", "Choisissez une reine déjà enregistrée.",
                )
        elif origine == "NOUVELLE":
            if not cleaned_data.get("identifiant"):
                self.add_error(
                    "identifiant",
                    "L'identifiant est obligatoire pour une nouvelle reine.",
                )
        return cleaned_data


class MarquerReineForm(forms.Form):
    """Page de confirmation du marquage d'une reine (issue #51), avec
    couleur de marquage obligatoire proposée selon l'année de naissance
    (issue #53) : date et couleur proposées par défaut, modifiables."""

    date_marquage = forms.DateField(
        label="Date de marquage",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    couleur_marquage = forms.ChoiceField(
        label="Couleur du marquage", choices=CouleurMarquage.choices,
    )

    def __init__(self, *args, reine=None, **kwargs):
        super().__init__(*args, **kwargs)
        if reine is not None and not self.is_bound:
            couleur_proposee = couleur_marquage_proposee(reine)
            if couleur_proposee:
                self.fields["couleur_marquage"].initial = couleur_proposee
