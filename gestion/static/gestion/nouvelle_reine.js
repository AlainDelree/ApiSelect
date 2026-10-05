/* Formulaire de remplacement de reine (issue #51) : amélioration
 * progressive, aucune ressource externe. Sans ce script, tous les
 * champs restent visibles et modifiables ; le serveur applique de
 * toute façon les mêmes règles de validation.
 *
 * - montre le bloc « reine existante » ou le bloc « nouvelle reine »
 *   selon le choix d'origine ;
 * - montre le bloc vendeur seulement pour un mode d'acquisition
 *   d'achat ;
 * - montre les champs date et couleur de marquage seulement si
 *   marquage effectué ; la couleur est proposée selon l'année de
 *   naissance et recalculée quand celle-ci change, tant que la
 *   couleur n'a pas été modifiée à la main (issue #53) ;
 * - propose un identifiant à partir de la mère choisie (réutilise la
 *   logique existante, cf. `selection.calculs.suggerer_identifiant_fille`),
 *   tant que l'autrice n'a pas elle-même modifié le champ.
 */
(function () {
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
