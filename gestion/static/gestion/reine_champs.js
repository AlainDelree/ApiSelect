/* Comportements communs aux formulaires de reine (issue #54) :
 * amélioration progressive, aucune ressource externe.
 *
 * - montre le bloc vendeur seulement pour un mode d'acquisition
 *   d'achat ;
 * - montre les champs date et couleur de marquage seulement si
 *   marquage effectué ; la couleur est proposée selon l'année de
 *   naissance et recalculée quand celle-ci change, tant que la
 *   couleur n'a pas été modifiée à la main (issue #53).
 *
 * Partagé par le formulaire de remplacement (`nouvelle_reine.js`,
 * issue #51) et le formulaire de création/modification unique
 * (`reine_form.js`, issue #54) — chargé avant eux sur la page.
 */
(function (window) {
    "use strict";

    var MODES_ACQUISITION_ACHAT = ["ACHETEE_CR", "ACHETEE_VIERGE", "ACHETEE_FECONDEE"];

    // Convention apicole : dernier chiffre de l'année de naissance ->
    // couleur de marquage. Doit rester cohérente avec
    // `gestion.couleurs.couleur_marquage_pour_annee` (cf. CouleurMarquage).
    var COULEUR_PAR_DERNIER_CHIFFRE_ANNEE = {
        1: "BLANC", 6: "BLANC",
        2: "JAUNE", 7: "JAUNE",
        3: "ROUGE", 8: "ROUGE",
        4: "VERT", 9: "VERT",
        5: "BLEU", 0: "BLEU",
    };

    function couleurMarquagePourAnnee(annee) {
        if (!annee) {
            return "";
        }
        var dernierChiffre = Number(String(annee).slice(-1));
        return COULEUR_PAR_DERNIER_CHIFFRE_ANNEE[dernierChiffre] || "";
    }

    function initialiserChampsReine(formulaire) {
        if (!formulaire) {
            return;
        }

        var radiosMode = formulaire.querySelectorAll('input[name="mode_acquisition"]');
        var blocVendeur = document.getElementById("bloc-vendeur");

        function mettreAJourVendeur() {
            var choix = formulaire.querySelector('input[name="mode_acquisition"]:checked');
            var estAchat = !!choix && MODES_ACQUISITION_ACHAT.indexOf(choix.value) !== -1;
            if (blocVendeur) {
                blocVendeur.style.display = estAchat ? "" : "none";
            }
        }

        radiosMode.forEach(function (radio) {
            radio.addEventListener("change", mettreAJourVendeur);
        });
        mettreAJourVendeur();

        var radiosMarquage = formulaire.querySelectorAll('input[name="marquage_effectue"]');
        var blocDateMarquage = document.getElementById("bloc-date-marquage");

        function mettreAJourDateMarquage() {
            var choix = formulaire.querySelector('input[name="marquage_effectue"]:checked');
            var effectue = !!choix && choix.value === "oui";
            if (blocDateMarquage) {
                blocDateMarquage.style.display = effectue ? "" : "none";
            }
        }

        radiosMarquage.forEach(function (radio) {
            radio.addEventListener("change", mettreAJourDateMarquage);
        });
        mettreAJourDateMarquage();

        var champDateNaissance = document.getElementById("id_date_naissance");
        var champCouleurMarquage = document.getElementById("id_couleur_marquage");
        var couleurModifieeParUtilisateur = false;

        if (champCouleurMarquage) {
            champCouleurMarquage.addEventListener("change", function () {
                couleurModifieeParUtilisateur = true;
            });
        }

        if (champDateNaissance && champCouleurMarquage) {
            champDateNaissance.addEventListener("change", function () {
                if (couleurModifieeParUtilisateur || !champDateNaissance.value) {
                    return;
                }
                var annee = champDateNaissance.value.slice(0, 4);
                var couleur = couleurMarquagePourAnnee(annee);
                if (couleur) {
                    champCouleurMarquage.value = couleur;
                }
            });
        }
    }

    window.initialiserChampsReine = initialiserChampsReine;
})(window);
