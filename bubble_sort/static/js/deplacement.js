// Au début de votre fichier
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');


var bubbleListUrl = $('#bubble-container').data('bubble-list-url');

// Fonction de throttling améliorée avec annulation
function throttle(func, limit) {
    let lastFunc;
    let lastRan;
    let timeoutId;

    const throttled = function() {
        const context = this;
        const args = arguments;

        if (!lastRan) {
            func.apply(context, args);
            lastRan = Date.now();
        } else {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(function() {
                if (Date.now() - lastRan >= limit) {
                    func.apply(context, args);
                    lastRan = Date.now();
                }
            }, limit - (Date.now() - lastRan));
        }
    };

    throttled.cancel = function() {
        clearTimeout(timeoutId);
    };

    return throttled;
}

// Créer une instance throttlée
const throttledUpdatePositions = throttle(updateOrder, 1000);


function saveBubbleData(bubble, field, value) {
    const bubbleId = bubble.data('id');

    $.ajax({
        url: bubbleListUrl,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            action: 'save_bubble_data',
            bubble_id: bubbleId,
            field: field,
            value: value
        }),
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            console.log(`${field} sauvegardé avec succès`);
        },
        error: function(xhr, status, error) {
            console.error(`Erreur lors de la sauvegarde du ${field}:`, error);
        }
    });
}


function updateSize(bubble) {
    // Dans updateSize()
    const bubbleId = parseInt(bubble.data('id'), 10); // Garantit un integer
    if (isNaN(bubbleId)) {
        console.error('ID de bulle invalide');
        return;
    }

    const width = Math.round(bubble.width());
    const height = Math.round(bubble.height());

    // Màj des données dans le DOM
    bubble.data({
        width: width,
        height: height
    });

    // Envoi au serveur
    $.ajax({
        url: bubbleListUrl,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            action: 'resize_bubble',
            bubble_id: bubbleId,
            width: width,
            height: height
        }),
        headers: { 'X-CSRFToken': csrftoken },
        success: function(response) {
            console.log('Dimensions sauvegardées:', response);
        }
    });
}


function updateBubbleNumbers() {
    $('.bubble').each(function(index) {
        $(this).find('.bubble-number').text(index + 1);
    });
}


function updateOrder() {
    const orderedIds = $(".bubble").map(function() {
        return parseInt($(this).data('id'), 10);
    }).get();

    $.ajax({
        url: bubbleListUrl,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            action: 'update_positions',
            positions: orderedIds  // Liste simple d'IDs [3, 8, 5...]
        }),
        headers: {'X-CSRFToken': csrftoken}
    });
}


// Correction de hexToRgb avec gestion des erreurs
function hexToRgb(hex) {
    if (!hex || typeof hex !== 'string' || !/^#([A-Fa-f0-9]{6})$/.test(hex)) {
        console.error('Code couleur hexadécimal invalide:', hex);
        return { r: 0, g: 0, b: 0 }; // Retourne du noir par défaut
    }

    try {
        return {
            r: parseInt(hex.substring(1, 3), 16),
            g: parseInt(hex.substring(3, 5), 16),
            b: parseInt(hex.substring(5, 7), 16)
        };
    } catch (e) {
        console.error('Erreur de conversion hex vers RGB:', e);
        return { r: 0, g: 0, b: 0 };
    }
}

// Modification de la récupération des couleurs
function getSelectedColor(selector) {
    const $select = $(selector);
    const selectedOption = $select.find('option:selected');
    return selectedOption.data('color-code') || '#000000'; // Fallback sécurisé
}

function mixColor(startHex, endHex, ratio) {
    const s = hexToRgb(startHex);
    const e = hexToRgb(endHex);
    const r = Math.round(s.r + (e.r - s.r) * ratio);
    const g = Math.round(s.g + (e.g - s.g) * ratio);
    const b = Math.round(s.b + (e.b - s.b) * ratio);

    return { r, g, b }; // Retourne un objet au lieu d'une chaîne
}

function updatePreview() {
    const startColor = $('#color-start option:selected').data('color-code');
    const endColor = $('#color-end option:selected').data('color-code');

    // Mise à jour uniquement des carrés de preview
    $('.color-preview').eq(0).css('background-color', startColor);
    $('.color-preview').eq(1).css('background-color', endColor);
}

// Modification de updateBubbleColors
function updateBubbleColors() {
    const start = getSelectedColor('#color-start');
    const end = getSelectedColor('#color-end');
    const bubbles = $('.bubble');

    bubbles.each(function(index) {
        const ratio = index / (bubbles.length - 1);
        const color = mixColor(start, end, ratio);
        const brightness = (color.r * 299 + color.g * 587 + color.b * 114) / 1000;

        $(this).css({
            'background-color': `rgb(${color.r}, ${color.g}, ${color.b})`,
            'color': brightness > 128 ? 'black' : 'white'
        });
    });
}


function elementsOverlap(element1, element2, threshold = 20) {

    if (!$.fn.sortable) {
        console.error("jQuery UI n'est pas chargé correctement");
        return;
    }
    console.log("Début de elementsOverlap");
    console.log("element1:", element1);
    console.log("element2:", element2);
    console.log("threshold:", threshold);

    // Vérification du type des éléments
    if (!(element1 instanceof jQuery) || !(element2 instanceof jQuery)) {
        console.error("Les éléments doivent être des objets jQuery");
        return false;
    }

    // Conversion en éléments DOM
    const el1 = element1.get(0);
    const el2 = element2.get(0);

    console.log("el1 (DOM):", el1);
    console.log("el2 (DOM):", el2);

    if (!el1 || !el2) {
        console.error("Un des éléments est null ou undefined");
        return false;
    }

    // Obtention des rectangles
    const rect1 = el1.getBoundingClientRect();
    const rect2 = el2.getBoundingClientRect();

    console.log("rect1:", rect1);
    console.log("rect2:", rect2);

    // Calcul du chevauchement
    const overlap = !(
        rect1.right < rect2.left + threshold ||
        rect1.left > rect2.right - threshold ||
        rect1.bottom < rect2.top + threshold ||
        rect1.top > rect2.bottom - threshold
    );

    console.log("Chevauchement détecté:", overlap);

    return overlap;
}

function saveColors() {
    const startColorId = $('#color-start').val();
    const endColorId = $('#color-end').val();

    $.ajax({
        url: bubbleListUrl,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            action: 'update_colors',
            start_color_id: startColorId,
            end_color_id: endColorId
        }),
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function(response) {
            if (response.status === 'success') {
                updateBubbleColors(); // Mise à jour immédiate des couleurs
                console.log('Couleurs mises à jour avec succès');
            } else {
                console.error('Erreur lors de la mise à jour:', response.message);
            }
        }
    });
}



// Créer une instance throttlée
const throttledUpdateOrder = throttle(updateOrder, 1000); // 1000ms = 1 seconde

$(function() {
    // Déclencheur sur changement de sélection
    updatePreview(); // Initialisation des previews
    $(".bubble").each(function() {
        // Récupère les valeurs directement depuis les attributs data-*
        const width = $(this).data('width'); // Plus de valeur par défaut
        const height = $(this).data('height');

        // Applique seulement si les valeurs existent
        if (width) $(this).css('width', width + 'px');
        if (height) $(this).css('height', height + 'px');
    });
    let isDragging = false;
    let draggedBubble = null;
    let updatePositionTimeout;


    const dragHandleSize = 20; // Taille de la zone de drag
    const handleSize = 20; // Taille de la zone de drag

    // Gestion du drag manuel
    $(".bubble").on('mousedown', function(e) {
        const $bubble = $(this);
        const $target = $(e.target);

        if ($target.closest('.resize-handle').length) {
            $bubble.resizable('enable');
            return false;
        }

        if ($target.closest('.drag-handle').length) {
            isDragging = true;
            draggedBubble = $bubble.addClass('dragging');
            $("#bubble-container").sortable("disable");
            return false;
        }
    }).resizable({
        handles: { 'se': '.resize-handle' },
        minHeight: 100,
        maxHeight: 600,
        minWidth: 100,
        maxWidth: 1300,
        start: function(e, ui) {
            $("#bubble-container").sortable("disable");
            $(this).addClass('resizing-active');
        },
        stop: function(e, ui) {
            const $bubble = $(this);
            updateSize($bubble); // Appel de la nouvelle fonction
            $bubble.removeClass('resizing-active');
            $("#bubble-container").sortable("enable");
        }
    });

    $(document).on('mousemove', function(e) {
    if (!isDragging || !draggedBubble) return;

        const $bubbles = $(".bubble").not(draggedBubble)
        const draggedRect = draggedBubble[0].getBoundingClientRect()

        $bubbles.each(function() {
            const $target = $(this)
            if (elementsOverlap(draggedBubble, $target)) {
                const targetMidY = $target.offset().top + ($target.outerHeight() / 2)
                const insertPosition = e.clientY < targetMidY ? 'before' : 'after'

                if ($target.data('lastInsertPosition') !== insertPosition) {
                    $target[insertPosition](draggedBubble)
                    $target.data('lastInsertPosition', insertPosition)
                    throttledUpdateOrder()
                }
            }
        })
    }).on('mouseup', function() {
            if (draggedBubble) {
                draggedBubble.removeClass('dragging');
                draggedBubble.find('.resize-handle').show();
            }
            isDragging = false;
            draggedBubble = null;
            throttledUpdateOrder.cancel(); // Utilisez la bonne variable
            throttledUpdatePositions.cancel(); // Annule le throttling
            updateOrder();
        });
     // Configuration du sortable
        $("#bubble-container").sortable({
            cancel: '.resize-handle, .drag-handle, textarea',
            items: '.bubble',
            update: function(event, ui) {
                const positions = $(this).sortable('toArray', { attribute: 'data-id' });
                $.ajax({
                    url: bubbleListUrl,
                    type: 'POST',
                    data: JSON.stringify({ action: 'update_positions', positions: positions }),
                    headers: { 'X-CSRFToken': csrftoken }
                });
            }
        });



    $('input[name="classement_name"]').on('input', function() {
    const newName = $(this).val().trim();

        // N'envoie la requête que si le nom n'est pas vide
        if (newName) {
            $.ajax({
                url: bubbleListUrl,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    action: 'update_name',
                    classement_name: newName
                }),
                headers: {
                    'X-CSRFToken': csrftoken
                },
                success: function(response) {
                    if (response.status === 'success') {
                        // Met à jour le titre H1 si nécessaire
                        $('h1').text(newName);
                    }
                }
            });
        }
    });

     // Gestion du redimensionnement au survol
    $(".resize-handle").hover(
        function() { $(this).closest('.bubble').resizable('enable'); },
        function() { $(this).closest('.bubble').resizable('disable'); }
    );

    // Écouteurs d'événements pour le contenu et le titre
    $(document).on('input', '.bubble textarea', function() {
        const bubble = $(this).closest('.bubble');
        saveBubbleData(bubble, 'content', $(this).val());
    });

    $(document).on('input', '.bubble .bubble-title', function() {
        const bubble = $(this).closest('.bubble');
        saveBubbleData(bubble, 'title', $(this).val());
    });

    $(document).on('click', '.delete-bubble', function(e) {
    e.stopPropagation();
    const bubble = $(this).closest('.bubble');
    const bubbleId = bubble.data('id');

    $.ajax({
        url: bubbleListUrl,
        type: 'POST',
        contentType: 'application/json', // <- Ajout crucial
        data: JSON.stringify({          // <- Format JSON
            action: 'delete_bubble',
            bubble_id: bubbleId
        }),
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function(response) {
            if (response.status === 'success') {
                bubble.remove();
                updateOrder();
                updateBubbleColors();
                updateBubbleNumbers();
                }
            },
            error: function(xhr) {
                console.error('Erreur détaillée:', xhr.responseText);
            }
        });
    });

    // Écouteur pour les changements
    $('.color-select').on('change', function() {
        $.ajax({
            url: bubbleListUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                action: 'update_colors',
                start_color_id: $('#color-start').val(),
                end_color_id: $('#color-end').val()
            }),
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(response) {
                if (response.status === 'success') {
                    updatePreview();
                    updateBubbleColors();
                }
            }
        });
    });

    updatePreview(); // Mise à jour des previews lors du changement
    updateBubbleColors(); // Mise à jour des bulles (fonction existante)
    updateBubbleNumbers();

});






