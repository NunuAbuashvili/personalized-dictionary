const container = document.querySelector(".container"),
  pwShowHide = document.querySelectorAll(".showHidePw"),
  pwFields = document.querySelectorAll(".password"),
  signUp = document.querySelector(".signup-link"),
  login = document.querySelector(".login-link");

// js code to show/hide password and change icon
pwShowHide.forEach((eyeIcon) => {
  eyeIcon.addEventListener("click", () => {
    pwFields.forEach((pwField) => {
      if (pwField.type === "password") {
        pwField.type = "text";

        pwShowHide.forEach((icon) => {
          icon.classList.replace("uil-eye-slash", "uil-eye");
        });
      } else {
        pwField.type = "password";

        pwShowHide.forEach((icon) => {
          icon.classList.replace("uil-eye", "uil-eye-slash");
        });
      }
    });
  });
});

let subMenu = document.getElementById("subMenu");

function toggleMenu(){
  subMenu.classList.toggle("open-menu");
}

document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.querySelector('input[name="{{ profile_form.image.name }}"]');
    const imagePreview = document.getElementById('profile-preview');

    if (imageInput) {
        imageInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });

    } else {
        console.error("Element with ID 'imageInput' not found.");
    }
});

function filterFolders(language) {
    const folderLinks = document.querySelectorAll('.dictionary-folder-link');

    folderLinks.forEach(link => {
        const folder = link.querySelector('.dictionary-folder');
        const folderLanguage = folder.getAttribute('data-language');

        if (language === 'All' || folderLanguage === language) {
            link.classList.remove('hidden');
        } else {
            link.classList.add('hidden');
        }
    });
}
