$(document).ready(function() {

    $("#slider").slider({
        animate: true,
        value:1,
        min: 0,
        max: 1000,
        step: 10,
        slide: function(event, ui) {
            update(1,ui.value); //changed
        }
    });
    update();
});

