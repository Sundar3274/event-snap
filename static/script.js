document.addEventListener('DOMContentLoaded', function() {
    ClassicEditor
        .create(document.querySelector('#event_description'))
        .then(editor => {
            document.querySelector('#event_description').value = editor.getData();
        })
        .catch(error => {
            console.error(error);
        });

    tinymce.init({
        selector: '#mytextarea',
        toolbar: 'undo redo | styles | bold italic | alignleft aligncenter alignright alignjustify | outdent indent',
        menubar: false,
        setup: function(editor) {
            editor.on('change', function() {
                editor.save();
            });
        }
    });

    document.getElementById('eventForm').addEventListener('submit', function(event) {
        validateDescriptionMatch();

        const descError = document.getElementById('desc-error').textContent;
        if (descError) {
            event.preventDefault();
        }
    });
});

function validateFileCount() {
    const fileInput = document.getElementById('photos');
    const fileError = document.getElementById('file-error');

    if (fileInput.files.length > 4) {
        fileError.textContent = "You can only upload a maximum of 4 images.";
        fileInput.value = '';
    } else {
        fileError.textContent = '';
    }

    validateDescriptionMatch();
}

function validateDescriptionMatch() {
    const fileInput = document.getElementById('photos');
    const descInput = document.getElementById('photo_desc');
    const descError = document.getElementById('desc-error');

    const descriptions = descInput.value.split(',').map(desc => desc.trim()).filter(desc => desc.length > 0);
    const photoCount = fileInput.files.length;

    if (photoCount > 0 && descriptions.length !== photoCount) {
        descError.textContent = `The number of descriptions (${descriptions.length}) does not match the number of uploaded photos (${photoCount}).`;
    } else {
        descError.textContent = '';
    }
}
