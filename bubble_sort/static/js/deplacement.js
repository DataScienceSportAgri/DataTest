var bubbleListUrl = $('#bubble-container').data('bubble-list-url');

$(function() {
    $.ajaxSetup({
        headers: { "X-CSRFToken": getCookie("csrftoken") }
    });

    let isDragging = false;
    let draggedBubble = null;

        $(".bubble").on('mousedown', function(e) {
        if (!$(e.target).hasClass('ui-resizable-handle') && !$(e.target).is('textarea') && !$(e.target).hasClass('bubble-number')) {
            isDragging = true;
            draggedBubble = $(this);
            $(this).addClass('dragging');
        }
    }).resizable({
        handles: {
            'se': '.resize-handle'
        },
        minHeight: 100,
        maxHeight: 300,
        minWidth: 100,
        maxWidth: 400,
        stop: function(event, ui) {
            updatePositions();
        }
    });

    $(document).on('mousemove', function(e) {
        if (!isDragging) return;

        // Votre code existant pour le déplacement et l'échange de positions
        $(".bubble").each(function() {
            if ($(this).is(draggedBubble)) return;

            let rect = this.getBoundingClientRect();
            let midY = rect.top + rect.height / 2;

            if (e.clientX > rect.left && e.clientX < rect.right &&
                e.clientY > rect.top && e.clientY < rect.bottom) {
                // Intervertir les positions
                let tempPosition = draggedBubble.data('position');
                draggedBubble.data('position', $(this).data('position'));
                $(this).data('position', tempPosition);

                // Échanger physiquement les bulles dans le DOM
                if (e.clientY < midY) {
                    $(this).before(draggedBubble);
                } else {
                    $(this).after(draggedBubble);
                }

                // Envoyer la mise à jour au serveur
                updatePositions();
            }
        });
    });

    $(document).on('mouseup', function() {
        if (draggedBubble) {
            draggedBubble.removeClass('dragging');
        }
        isDragging = false;
        draggedBubble = null;
    });

    // Gestionnaire d'événements pour la suppression de bulle
    $(document).on('click', '.delete-bubble', function(e) {
    console.log('Delete button clicked');

        e.stopPropagation(); // Empêche le déclenchement de l'événement sur la bulle parente
        var bubble = $(this).closest('.bubble');
        var bubbleId = bubble.data('id');

        if (confirm('Êtes-vous sûr de vouloir supprimer cette bulle ?')) {
            $.post(bubbleListUrl, {
                action: 'delete_bubble',
                bubble_id: bubbleId,
                csrfmiddlewaretoken: '{{ csrf_token }}'
            }, function(response) {
                if (response.status === 'success') {
                    bubble.remove();
                    updatePositions();
                    updateBubbleColors();
                    updateBubbleNumbers();
                } else {
                    alert('Erreur lors de la suppression de la bulle');
                }
            });
        }
    });
        // Fonction pour sauvegarder le contenu d'une bulle
    function saveBubbleContent(bubble) {
        var content = bubble.find('textarea').val();
        var bubbleId = bubble.data('id');

        $.post(bubbleListUrl, {
            action: 'save_bubble_content',
            bubble_id: bubbleId,
            content: content,
            csrfmiddlewaretoken: '{{ csrf_token }}'
        });
    }

    // Utiliser l'événement 'input' pour détecter les changements dans le textarea
    $(document).on('input', '.bubble textarea', function() {
        var bubble = $(this).closest('.bubble');
        saveBubbleContent(bubble);
    });

    function updateBubbleNumbers() {
        $('.bubble').each(function(index) {
            $(this).find('.bubble-number').text(index + 1);
        });
    }


    function updatePositions() {
        var positions = $(".bubble").map(function() {
            return {
                id: $(this).data('id'),
                position: $(this).index(),
                width: $(this).width(),
                height: $(this).height()
            };
        }).get();

        $.post(bubbleListUrl, {
            positions: JSON.stringify(positions),
            csrfmiddlewaretoken: '{{ csrf_token }}'
        }).done(function() {
            updateBubbleColors();
                updateBubbleNumbers();
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

    // Appeler updateBubbleColors initialement
    updateBubbleColors();
    updateBubbleNumbers();

});
