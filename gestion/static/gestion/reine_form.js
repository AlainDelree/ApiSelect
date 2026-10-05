/* Formulaire unique de création/modification d'une reine (issue #54) :
 * amélioration progressive, aucune ressource externe. Les
 * comportements communs (vendeur, date et couleur de marquage) sont
 * factorisés dans `reine_champs.js`, chargé avant ce script.
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        var formulaire = document.getElementById("formulaire-reine");
        if (formulaire && window.initialiserChampsReine) {
            window.initialiserChampsReine(formulaire);
        }
    });
})();
