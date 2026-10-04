/* Formulaire de saisie de visite (issue #45) : amélioration progressive,
 * aucune ressource externe. Sans ce script, le champ « Date de
 * revérification » reste simplement toujours visible et modifiable ;
 * le serveur applique de toute façon visite + 9 jours s'il est vide.
 *
 * - affiche le champ seulement quand « Reine morte » est en doute ;
 * - propose automatiquement visite + 9 jours, et recalcule cette
 *   proposition quand la date de la visite change, tant que l'autrice
 *   n'a pas elle-même modifié le champ.
 */
(function () {
    "use strict";

    var DELAI_RAPPEL_REINE_MORTE_JOURS = 9;

    function ajouterJours(dateIso, jours) {
        var date = new Date(dateIso + "T00:00:00");
        if (isNaN(date.getTime())) {
            return "";
        }
        date.setDate(date.getDate() + jours);
        return date.toISOString().slice(0, 10);
    }

    document.addEventListener("DOMContentLoaded", function () {
        var champDateVisite = document.getElementById("id_date");
        var champDateReverification = document.getElementById(
            "id_date_reverification_reine_morte"
        );
        var radiosReineMorte = document.querySelectorAll(
            'input[name="observation_reine_morte"]'
        );
        if (!champDateVisite || !champDateReverification || !radiosReineMorte.length) {
            return;
        }
        var sousQuestion = champDateReverification.closest(".sous-question");
        var modifieeParUtilisateur = false;

        champDateReverification.addEventListener("input", function () {
            modifieeParUtilisateur = true;
        });

        function recalculerDateProposee() {
            if (modifieeParUtilisateur || !champDateVisite.value) {
                return;
            }
            champDateReverification.value = ajouterJours(
                champDateVisite.value, DELAI_RAPPEL_REINE_MORTE_JOURS
            );
        }

        function estEnDoute() {
            var choix = document.querySelector(
                'input[name="observation_reine_morte"]:checked'
            );
            return !!choix && choix.value === "DOUTE";
        }

        function mettreAJourAffichage() {
            var visible = estEnDoute();
            if (sousQuestion) {
                sousQuestion.style.display = visible ? "" : "none";
            }
            if (visible) {
                recalculerDateProposee();
            }
        }

        champDateVisite.addEventListener("change", recalculerDateProposee);
        radiosReineMorte.forEach(function (radio) {
            radio.addEventListener("change", mettreAJourAffichage);
        });

        mettreAJourAffichage();
    });
})();
