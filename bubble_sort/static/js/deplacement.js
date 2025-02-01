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


function saveBubbleContent(bubble) {
    var content = bubble.find('textarea').val();
    var bubbleId = bubble.data('id');

    $.ajax({
        url: bubbleListUrl,
        type: 'POST',
        data: JSON.stringify({
            action: 'save_bubble_content',
            bubble_id: bubbleId,
            content: content
        }),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            console.log('Contenu sauvegardé avec succès');
        },
        error: function(xhr, status, error) {
            console.error('Erreur lors de la sauvegarde:', error);
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




function updateBubbleColors() {
    const bubbles = $('.bubble');
    const totalBubbles = bubbles.length;

    bubbles.each(function(index) {
        const ratio = index / (totalBubbles - 1);
        const r = Math.round(255 * ratio);
        const g = Math.round(255 * (1 - ratio));
        const b = 0;

        $(this).css('background-color', `rgb(${r}, ${g}, ${b})`);

        const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        $(this).css('color', brightness > 128 ? 'black' : 'white');
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




$(function() {
    let isDragging = false;
    let draggedBubble = null;
    let updatePositionTimeout;
    let updateTimeout;
    // Après la déclaration de updateOrder
    const throttledUpdateOrder = throttle(updateOrder, 1000); // 1000ms = 1 seconde

    const updateDelay = 1000; // 1 seconde

    $("#bubble-container").sortable({
        update: function() {
            clearTimeout(updateTimeout);
            updateTimeout = setTimeout(updateOrder, updateDelay);
        }
    });


    $(".bubble").on('mousedown', function(e) {
    const $bubble = $(this);
    const handleSize = 20;
    const bubbleRight = $bubble.offset().left + $bubble.outerWidth();
    const bubbleBottom = $bubble.offset().top + $bubble.outerHeight();

    if (e.pageX > bubbleRight - handleSize && e.pageY > bubbleBottom - handleSize) {
        $bubble.addClass('resizing');
        $bubble.resizable('enable');
        return false;
    }

    if (!$(e.target).closest('.no-drag, textarea').length) {
        isDragging = true;
        draggedBubble = $bubble.addClass('dragging');
        $bubble.find('.resize-handle').hide();
    }
    }).resizable({
        handles: { 'se': '.resize-handle' },
        minHeight: 100,
        maxHeight: 300,
        minWidth: 100,
        maxWidth: 400,
        start: function(e, ui) {
            // Début du redimensionnement
            $(this).css("position", "").addClass('resizing-active');
            },
        stop: function(e, ui) {
            // Fin du redimensionnement
            const bubble = $(this);

            // 1. Mettre à jour l'ordre
            updateOrder();

            // 2. Envoyer les nouvelles dimensions
            $.ajax({
                url: bubbleListUrl,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    action: 'resize_bubble',
                    bubble_id: bubble.data('id'),
                    width: bubble.width(),
                    height: bubble.height()
                }),
                headers: { 'X-CSRFToken': csrftoken }
            });

            // 3. Retirer les classes
            bubble.removeClass('resizing-active');

            // 4. Throttling pour les mises à jour visuelles
            throttledUpdateOrder();
        }
    });


    $(document).on('mousemove', function(e) {
    if (!isDragging || !draggedBubble) return

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
            throttledUpdatePositions.cancel(); // Annule le throttling
            updateOrder();
        });


            // Utiliser l'événement 'input' pour détecter les changements dans le textarea
    $(document).on('input', '.bubble textarea', function() {
        var bubble = $(this).closest('.bubble');
        saveBubbleContent(bubble);
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
        // Appeler updateBubbleColors initialement
    updateBubbleColors();
    updateBubbleNumbers();

});






