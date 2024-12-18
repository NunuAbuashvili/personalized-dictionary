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

function showAllDictionaries() {
    console.log("Showing all dictionaries");
}

function filterFolders(language) {
    const folders = document.querySelectorAll('.dictionary-folder');
    const filterButtons = document.querySelectorAll('.filter-btn');

    // Reset active state on all buttons
    filterButtons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    folders.forEach(folder => {
        if (language === 'All' || folder.dataset.language === language) {
            folder.style.display = 'block';
        } else {
            folder.style.display = 'none';
        }
    });
}
