/* Formulaire de remplacement de reine (issue #51) : amélioration
 * progressive, aucune ressource externe. Sans ce script, tous les
 * champs restent visibles et modifiables ; le serveur applique de
 * toute façon les mêmes règles de validation.
 *
 * - montre le bloc « reine existante » ou le bloc « nouvelle reine »
 *   selon le choix d'origine ;
 * - propose un identifiant à partir de la mère choisie (réutilise la
 *   logique existante, cf. `selection.calculs.suggerer_identifiant_fille`),
 *   tant que l'autrice n'a pas elle-même modifié le champ ;
 * - les comportements communs aux champs de la reine (vendeur, date
 *   et couleur de marquage) sont factorisés dans `reine_champs.js`
 *   (issue #54), chargé avant ce script.
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        var formulaire = document.getElementById("formulaire-nouvelle-reine");
        if (!formulaire) {
            return;
        }

        var radiosOrigine = formulaire.querySelectorAll('input[name="origine"]');
        var blocExistante = document.getElementById("bloc-reine-existante");
        var blocNouvelle = document.getElementById("bloc-nouvelle-reine");

        function origineChoisie() {
            var choix = formulaire.querySelector('input[name="origine"]:checked');
            return choix ? choix.value : "";
        }

        function mettreAJourOrigine() {
            var nouvelle = origineChoisie() === "NOUVELLE";
            if (blocExistante) {
                blocExistante.style.display = nouvelle ? "none" : "";
            }
            if (blocNouvelle) {
                blocNouvelle.style.display = nouvelle ? "" : "none";
            }
        }

        radiosOrigine.forEach(function (radio) {
            radio.addEventListener("change", mettreAJourOrigine);
        });
        mettreAJourOrigine();

        if (window.initialiserChampsReine) {
            window.initialiserChampsReine(formulaire);
        }

        var champMere = document.getElementById("id_mere");
        var champIdentifiant = document.getElementById("id_identifiant");
        var champDateRemplacement = document.getElementById("id_date_remplacement");
        var modifieParUtilisateur = false;

        if (champIdentifiant) {
            champIdentifiant.addEventListener("input", function () {
                modifieParUtilisateur = true;
            });
        }

        if (champMere && champIdentifiant && champDateRemplacement) {
            champMere.addEventListener("change", function () {
                if (modifieParUtilisateur || !champMere.value || !champDateRemplacement.value) {
                    return;
                }
                var annee = champDateRemplacement.value.slice(0, 4);
                var url = formulaire.dataset.urlSuggestion
                    + "?mere_id=" + encodeURIComponent(champMere.value)
                    + "&annee=" + encodeURIComponent(annee);
                fetch(url)
                    .then(function (reponse) { return reponse.json(); })
                    .then(function (donnees) {
                        if (!modifieParUtilisateur && donnees.identifiant) {
                            champIdentifiant.value = donnees.identifiant;
                        }
                    })
                    .catch(function () {});
            });
        }
    });
})();
