const password = document.getElementById("password");
const togglePassword = document.getElementById("togglePassword");

togglePassword.addEventListener("click", function () {
    if (password.type === "password") {
        password.type = "text";
        togglePassword.textContent = "Hide";
    } else {
        password.type = "password";
        togglePassword.textContent = "Show";
    }
});


const roleOptions = document.querySelectorAll(".role-option");
const selectedRole = document.getElementById("selectedRole");

roleOptions.forEach(function (roleButton) {

    roleButton.addEventListener("click", function () {

        roleOptions.forEach(function (button) {
            button.classList.remove("active");
        });

        roleButton.classList.add("active");

        selectedRole.value = roleButton.dataset.role;

    });

});


const loginForm = document.getElementById("loginForm");
const email = document.getElementById("email");


loginForm.addEventListener("submit", function (event) {

    event.preventDefault();

    const emailValue = email.value.trim();
    const passwordValue = password.value.trim();
    const roleValue = selectedRole.value;

    if (emailValue === "") {
        alert("Please enter your email.");
        email.focus();
        return;
    }

    if (!emailValue.includes("@")) {
        alert("Please enter a valid email address.");
        email.focus();
        return;
    }

    if (passwordValue === "") {
        alert("Please enter your password.");
        password.focus();
        return;
    }

    if (passwordValue.length < 6) {
        alert("Password must be at least 6 characters.");
        password.focus();
        return;
    }

    console.log("Login attempt");
    console.log("Email:", emailValue);
    console.log("Role:", roleValue);

    if (roleValue === "trainee") {
        window.location.href = "dashboard.html";
    }

    else if (roleValue === "trainer") {
        window.location.href = "trainer-dashboard.html";
    }

    else if (roleValue === "admin") {
        window.location.href = "admin-dashboard.html";
    }

});


const googleLogin = document.getElementById("googleLogin");

googleLogin.addEventListener("click", function () {

    const roleValue = selectedRole.value;

    console.log("Google login selected");
    console.log("Selected role:", roleValue);

    alert(
        "Google login for " +
        roleValue.charAt(0).toUpperCase() +
        roleValue.slice(1) +
        " will be connected to the backend later."
    );

});