'use strict';

/* Admin Ruche — couleur (issue #41) : ajoute un sélecteur natif
 * <input type="color"> à côté du champ texte réel (`id_couleur`), par
 * confort de saisie. Le champ texte reste la seule valeur soumise au
 * formulaire : un <input type="color"> ne peut pas rester vide (il
 * retombe sur #000000 dès qu'on le lit), donc on ne le branche jamais
 * comme widget direct — seulement comme aide visuelle synchronisée. */
(function () {
    var MOTIF_HEX = /^#[0-9A-Fa-f]{6}$/;

    document.addEventListener('DOMContentLoaded', function () {
        var champTexte = document.getElementById('id_couleur');
        if (!champTexte || champTexte.dataset.selecteurAjoute) {
            return;
        }
        champTexte.dataset.selecteurAjoute = '1';

        var selecteur = document.createElement('input');
        selecteur.type = 'color';
        selecteur.style.marginLeft = '0.5em';
        selecteur.style.verticalAlign = 'middle';
        selecteur.value = MOTIF_HEX.test(champTexte.value) ? champTexte.value : '#ffffff';

        selecteur.addEventListener('input', function () {
            champTexte.value = selecteur.value;
        });
        champTexte.addEventListener('input', function () {
            if (MOTIF_HEX.test(champTexte.value)) {
                selecteur.value = champTexte.value;
            }
        });

        champTexte.insertAdjacentElement('afterend', selecteur);
    });
})();
