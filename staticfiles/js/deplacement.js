
$(function() {
    let isDragging = false;
    let draggedBubble = null;

    $(".bubble").on('mousedown', function(e) {
        isDragging = true;
        draggedBubble = $(this);
        $(this).addClass('dragging');
    });

    $(document).on('mousemove', function(e) {
        if (!isDragging) return;

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


    function updatePositions() {
        var positions = $(".bubble").map(function() {
            return $(this).data('id');
        }).get();

        $.post("{% url 'update_positions' %}", {
            positions: positions.join(','),
            csrfmiddlewaretoken: '{{ csrf_token }}'
        }).done(function() {
            updateBubbleColors(); // Appeler updateBubbleColors après la mise à jour des positions
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
});
