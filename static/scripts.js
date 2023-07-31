$(document).ready(function() {

    new EmojiPicker({
        trigger: [
            {
                insertInto: ['#contact'],
                selector: '.emoji-button1'
            },
            {
                insertInto: ['#message'],
                selector: '.emoji-button2'
            }
        ],
    })

    // Detect language and set directionality dynamically
    $("#contact, #message, #contact_us_message").on("input", function() {
        var text = $(this).val();
        var lang = detectLanguage(text);
        setDirectionality($(this), lang);
    });

    function detectLanguage(text) {
        // Implement your language detection logic here
        // You can use external libraries or APIs for more accurate language detection
        // For simplicity, this example assumes English for text containing only ASCII characters
        // and Hebrew for text containing any non-ASCII Hebrew characters
        var regexHebrew = /[\u0590-\u05FF]/;
        if (regexHebrew.test(text)) {
            return "hebrew";
        } else {
            return "english";
        }
    }

    function setDirectionality(element, lang) {
        if (lang === "hebrew") {
            element.css("direction", "rtl");
            element.css("text-align", "right");
        } else {
            element.css("direction", "ltr");
            element.css("text-align", "left");
        }
    }

    // Bind the form submission event
    $("form").on("submit", function() {
        // Show the dot-spinner
        $(".loader").css("display", "flex");
    });

    $('#checkbox').change(function() {
        if (this.checked) {
            $('#submitButton').click();
        }
    });
});