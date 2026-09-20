"use strict";

/*
 * ============================================================
 * ADHYAN — SECURE LOGIN CLIENT
 * ============================================================
 *
 * Authentication:
 *   POST /auth/login
 *   GET  /auth/me
 *
 * Security:
 *   - No passwords in localStorage
 *   - No JWT stored in JavaScript
 *   - HttpOnly session cookie handles authentication
 *   - CSRF token is sent for state-changing requests
 *   - Server role is authoritative
 *
 * Demo login:
 *   Uses the SAME /auth/login endpoint.
 * ============================================================
 */


// ============================================================
// Configuration
// ============================================================

const API_BASE_URL =
    window.ADHYAN_API_URL ||
    (
        window.location.hostname === "localhost"
            ? "http://localhost:8000"
            : "http://127.0.0.1:8000"
    );


/*
 * ============================================================
 * DEMO ACCOUNT
 * ============================================================
 *
 * This must match the account created through:
 *
 * POST /auth/register
 *
 * Email:
 *   demo@adhyan.com
 *
 * Password:
 *   DemoPassword123!
 *
 * Name:
 *   Adhyan Demo Student
 *
 * IMPORTANT:
 * This is intentionally a normal TRAINEE account.
 */

const DEMO_EMAIL = "demo@adhyan.com";
const DEMO_PASSWORD = "DemoPassword123!";


// ============================================================
// DOM
// ============================================================

const loginForm =
    document.getElementById("loginForm");

const emailInput =
    document.getElementById("email");

const passwordInput =
    document.getElementById("password");

const togglePasswordButton =
    document.getElementById("togglePassword");

const forgotPasswordButton =
    document.getElementById("forgotPassword");

const googleLoginButton =
    document.getElementById("googleLogin");

const demoLoginButton =
    document.getElementById("demoLogin");

const loginButton =
    document.querySelector(".login-btn");

const statusElement =
    document.getElementById("status");

const loginText =
    document.getElementById("loginText");

const roleHint =
    document.getElementById("roleHint");

const roleButtons =
    document.querySelectorAll("[data-role]");


// ============================================================
// State
// ============================================================

let selectedRole = "trainee";
let loginInProgress = false;


// ============================================================
// Status
// ============================================================

function setStatus(message, type = "") {
    if (!statusElement) {
        return;
    }

    statusElement.textContent = message;
    statusElement.className = "status show";

    if (type) {
        statusElement.classList.add(type);
    }
}


function clearStatus() {
    if (!statusElement) {
        return;
    }

    statusElement.textContent = "";
    statusElement.className = "status";
}


// ============================================================
// Loading state
// ============================================================

function setLoading(isLoading, text = "Enter Adhyan") {
    loginInProgress = isLoading;

    if (loginButton) {
        loginButton.disabled = isLoading;

        loginButton.setAttribute(
            "aria-busy",
            String(isLoading)
        );
    }

    if (demoLoginButton) {
        demoLoginButton.disabled = isLoading;

        demoLoginButton.setAttribute(
            "aria-busy",
            String(isLoading)
        );
    }

    if (loginText) {
        loginText.textContent =
            isLoading
                ? text
                : "Enter Adhyan";
    }
}


// ============================================================
// Validation
// ============================================================

function isValidEmail(email) {
    if (!email || email.length > 320) {
        return false;
    }

    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}


// ============================================================
// CSRF
// ============================================================

function getCsrfToken() {
    const cookies =
        document.cookie.split(";");

    for (const cookie of cookies) {
        const trimmed = cookie.trim();

        if (trimmed.startsWith("adhyan_csrf=")) {
            return decodeURIComponent(
                trimmed.substring("adhyan_csrf=".length)
            );
        }
    }

    return null;
}


// ============================================================
// JSON helper
// ============================================================

function safeJsonParse(responseText) {
    if (!responseText) {
        return null;
    }

    try {
        return JSON.parse(responseText);
    } catch {
        return null;
    }
}


// ============================================================
// API
// ============================================================

async function apiRequest(
    endpoint,
    options = {}
) {
    const method =
        (options.method || "GET").toUpperCase();

    const headers =
        new Headers(options.headers || {});

    if (
        options.body &&
        !headers.has("Content-Type")
    ) {
        headers.set(
            "Content-Type",
            "application/json"
        );
    }


    /*
     * CSRF protection for state-changing requests.
     */

    if (
        method !== "GET" &&
        method !== "HEAD" &&
        method !== "OPTIONS"
    ) {
        const csrfToken =
            getCsrfToken();

        if (csrfToken) {
            headers.set(
                "X-CSRF-Token",
                csrfToken
            );
        }
    }


    const response =
        await fetch(
            `${API_BASE_URL}${endpoint}`,
            {
                ...options,

                method,
                headers,

                /*
                 * Required for HttpOnly session cookies.
                 */
                credentials: "include",

                cache: "no-store",
            }
        );


    const responseText =
        await response.text();

    const data =
        safeJsonParse(responseText);


    if (!response.ok) {
        const error =
            new Error("API request failed");

        error.status =
            response.status;

        error.data =
            data;

        throw error;
    }

    return data;
}


// ============================================================
// Role selector
// ============================================================

function setupRoleSelector() {
    roleButtons.forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                const role =
                    button.dataset.role;

                if (!role) {
                    return;
                }

                selectedRole = role;

                roleButtons.forEach(
                    (otherButton) => {
                        otherButton.classList.toggle(
                            "active",
                            otherButton === button
                        );
                    }
                );

                if (roleHint) {
                    roleHint.textContent =
                        button.dataset.hint ||
                        "Continue";
                }
            }
        );
    });
}


// ============================================================
// Password visibility
// ============================================================

function setupPasswordToggle() {
    if (
        !togglePasswordButton ||
        !passwordInput
    ) {
        return;
    }

    togglePasswordButton.addEventListener(
        "click",
        () => {
            const showing =
                passwordInput.type === "text";

            passwordInput.type =
                showing
                    ? "password"
                    : "text";

            togglePasswordButton.textContent =
                showing
                    ? "Show"
                    : "Hide";

            togglePasswordButton.setAttribute(
                "aria-pressed",
                String(!showing)
            );
        }
    );
}


// ============================================================
// Authentication verification
// ============================================================

async function getAuthenticatedUser() {
    const user =
        await apiRequest("/auth/me");

    if (
        !user ||
        !user.id ||
        !user.role
    ) {
        throw new Error(
            "Authentication verification failed"
        );
    }

    if (
        user.role !== "trainee" &&
        user.role !== "trainer" &&
        user.role !== "admin"
    ) {
        throw new Error(
            "Invalid account configuration"
        );
    }

    return user;
}


// ============================================================
// Normal login
// ============================================================

async function handleLogin(event) {
    event.preventDefault();

    if (loginInProgress) {
        return;
    }

    clearStatus();

    const isDemoSubmit = event.submitter?.id === "demoLogin";
    if (isDemoSubmit) {
        emailInput.value = DEMO_EMAIL;
        passwordInput.value = DEMO_PASSWORD;
    }

    const email =
        emailInput?.value
            ?.trim()
            .toLowerCase() || "";


    /*
     * NEVER trim passwords.
     */

    const password =
        passwordInput?.value || "";


    if (!isValidEmail(email)) {
        setStatus(
            "Please enter a valid email address.",
            "error"
        );

        emailInput?.focus();

        return;
    }


    if (!password) {
        setStatus(
            "Please enter your password.",
            "error"
        );

        passwordInput?.focus();

        return;
    }


    setLoading(
        true,
        "Signing in..."
    );


    try {

        /*
         * selectedRole is intentionally NOT sent.
         *
         * Backend decides the actual role.
         */

        await apiRequest(
            "/auth/login",
            {
                method: "POST",

                body: JSON.stringify({
                    email,
                    password,
                }),
            }
        );


        const user =
            await getAuthenticatedUser();


        redirectByRole(user.role);

    } catch (error) {

        console.error(
            "Login failed:",
            error
        );

        showLoginError(error);

    } finally {

        setLoading(false);
    }
}


// ============================================================
// Demo login
// ============================================================
async function handleDemoLogin() {
    if (loginInProgress) {
        return;
    }

    if (emailInput) {
        emailInput.value = DEMO_EMAIL;
    }
    if (passwordInput) {
        passwordInput.value = DEMO_PASSWORD;
    }

    await handleLogin({
        preventDefault() {},
    });
}


// ============================================================
// Error handling
// ============================================================

function showLoginError(error) {

    if (error.status === 401) {

        setStatus(
            "Invalid email or password.",
            "error"
        );

    } else if (error.status === 403) {

        setStatus(
            "Access denied.",
            "error"
        );

    } else if (error.status === 422) {

        setStatus(
            "Please check your login details.",
            "error"
        );

    } else if (error.status >= 500) {

        setStatus(
            "Adhyan is temporarily unavailable. Please try again.",
            "error"
        );

    } else {

        setStatus(
            "Unable to connect to Adhyan. Please try again.",
            "error"
        );
    }
}


// ============================================================
// Navigation
// ============================================================

function redirectByRole(role) {

    const destinations = {
        trainee: "dashboard.html",
    };


    const destination =
        destinations[role];


    if (!destination) {

        setStatus(
            "Unable to determine account destination.",
            "error"
        );

        return;
    }


    window.location.assign(
        destination
    );
}


// ============================================================
// Forgot password
// ============================================================

function setupForgotPassword() {

    if (!forgotPasswordButton) {
        return;
    }


    forgotPasswordButton.addEventListener(
        "click",
        () => {

            setStatus(
                "Password recovery will be available soon.",
                "info"
            );
        }
    );
}


// ============================================================
// Google login
// ============================================================

function setupGoogleLogin() {

    if (!googleLoginButton) {
        return;
    }


    googleLoginButton.addEventListener(
        "click",
        () => {

            setStatus(
                "Google sign-in will be connected after OAuth is configured.",
                "info"
            );
        }
    );
}


// ============================================================
// Demo button
// ============================================================

function setupDemoLogin() {

    if (!demoLoginButton) {
        console.warn(
            "Demo login button #demoLogin was not found."
        );

        return;
    }


    demoLoginButton.setAttribute("aria-label", "Enter Adhyan demo mode");
    demoLoginButton.addEventListener("click", (event) => {
        event.preventDefault();
        handleDemoLogin();
    });
}


// ============================================================
// Existing session
// ============================================================

async function checkExistingSession() {

    try {

        const user =
            await getAuthenticatedUser();

        redirectByRole(user.role);

    } catch {

        /*
         * No valid session.
         *
         * Normal on login page.
         */
    }
}


// ============================================================
// Form
// ============================================================

function setupLoginForm() {

    if (!loginForm) {
        return;
    }


    loginForm.addEventListener(
        "submit",
        handleLogin
    );
}


// ============================================================
// Initialize
// ============================================================

function initializeLoginPage() {

    setupRoleSelector();

    setupPasswordToggle();

    setupForgotPassword();

    setupGoogleLogin();

    setupDemoLogin();

    setupLoginForm();


    window.setTimeout(
        checkExistingSession,
        50
    );
}


// ============================================================
// Start
// ============================================================

if (
    document.readyState === "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        initializeLoginPage,
        {
            once: true,
        }
    );

} else {

    initializeLoginPage();
}