/* ============================================================
   ADHYAN DASHBOARD
   Connected to FastAPI + PostgreSQL
   ============================================================ */

const API_URL =
    window.ADHYAN_API_URL ||
    (
        window.location.hostname === "localhost"
            ? "http://localhost:8000"
            : "http://127.0.0.1:8000"
    );

let currentUser = null;
let currentStudent = null;
let currentSubjects = [];
let currentProgress = [];
let currentRecommendation = null;
let focusTimer = null;
let focusSeconds = 25 * 60;
let practiceQuestions = [];
let practiceIndex = 0;


/* ============================================================
   HELPERS
   ============================================================ */

function getCookie(name) {
    const cookies = document.cookie.split(";");

    for (const cookie of cookies) {
        const [key, ...value] = cookie.trim().split("=");

        if (key === name) {
            return decodeURIComponent(value.join("="));
        }

    }

    return null;
}

function updateFocusCountdown() {
    const element = document.getElementById("focus-countdown");
    if (!element) return;
    const minutes = Math.floor(focusSeconds / 60);
    const seconds = focusSeconds % 60;
    element.textContent = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function configureAdaptiveFocus() {
    const length = document.getElementById("focus-length");
    const button = document.getElementById("focus-timer-button");
    if (!length || !button) return;

    const mastery = currentRecommendation?.explanation?.signals?.mastery ?? 0;
    const action = currentRecommendation?.action;
    const selected = Number(length.value);
    const adaptiveLength = action === "CHALLENGE" && mastery >= 70
        ? Math.max(selected, 35)
        : action === "SIMPLIFY" || action === "EXPLAIN"
            ? Math.min(selected, 25)
            : selected;

    length.value = String(adaptiveLength);
    focusSeconds = adaptiveLength * 60;
    updateFocusCountdown();
    button.textContent = "Start adaptive focus";
}

function renderSessionChunk() {
    if (!currentRecommendation) return;
    const subject = currentRecommendation.subject?.name || currentRecommendation.subject || "Your subject";
    const topic = currentRecommendation.topic || subject;
    const action = formatAction(currentRecommendation.action);
    setText("session-title", `${action} ${subject} chunk`);
    setText(
        "session-plan",
        currentRecommendation.content ||
            `Spend this focus block on ${topic}. Finish with one small edge-case check.`
    );
    setText("session-subject", subject);
    setText("session-topic", `Topic: ${topic}`);
    setText("session-action", action);
    setText(
        "ai-explanation",
        currentRecommendation.explanation?.summary ||
            `This ${action.toLowerCase()} chunk was selected from your current progress.`
    );
}

function stopFocusSession() {
    if (focusTimer) {
        clearInterval(focusTimer);
        focusTimer = null;
    }
    const length = Number(document.getElementById("focus-length")?.value || 25);
    focusSeconds = length * 60;
    updateFocusCountdown();
    setText("session-title", "Session stopped");
    setText("session-plan", "Your focus session was stopped. Start a new chunk whenever you are ready.");
    const button = document.getElementById("focus-timer-button");
    if (button) {
        button.disabled = false;
        button.textContent = "Start focus chunk";
    }
    const sessionButton = document.getElementById("start-ai-session");
    if (sessionButton) {
        sessionButton.disabled = false;
        sessionButton.textContent = "Start Recommended Session →";
    }
}

function toggleFocusTimer() {
    const button = document.getElementById("focus-timer-button");
    if (!button) return;

    if (focusTimer) {
        clearInterval(focusTimer);
        focusTimer = null;
        button.textContent = "Resume adaptive focus";
        return;
    }

    button.textContent = "Pause focus";
    focusTimer = setInterval(() => {
        focusSeconds -= 1;
        updateFocusCountdown();
        if (focusSeconds <= 0) {
            clearInterval(focusTimer);
            focusTimer = null;
            button.textContent = "Break recommended";
            setText("ai-explanation", "Focus block complete. Take a short break, then let Adhyan reassess your next step.");
        }
    }, 1000);
}

async function analyzeMistake(event) {
    event.preventDefault();
    const input = document.getElementById("coach-message");
    const responseElement = document.getElementById("coach-response");
    if (!input || !responseElement || !input.value.trim()) return;

    responseElement.textContent = "Analyzing your mistake...";
    try {
        const response = await apiFetch("/api/coach/mistake", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: input.value.trim(),
                subject: currentRecommendation?.subject?.name || null,
            }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Mistake analysis failed.");
        responseElement.textContent = data.content;
    } catch (error) {
        responseElement.textContent = error.message || "Mistake analysis unavailable.";
    }
}

async function askLearningQuestion(event) {
        event.preventDefault();
        const input = document.getElementById("doubt-message");
        const responseElement = document.getElementById("doubt-response");
        const submitButton = document.getElementById("doubt-submit");
        if (!input || !responseElement || !input.value.trim()) return;
        responseElement.textContent = "Thinking...";
        submitButton?.setAttribute("disabled", "disabled");
        try {
            const response = await apiFetch("/api/coach/ask", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    message: input.value.trim(),
                    subject: currentRecommendation?.subject?.name || null,
                }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Doubt answer failed.");
            responseElement.textContent = data.content;
        } catch (error) {
            responseElement.textContent = error.message || "Doubt service unavailable.";
        } finally {
            submitButton?.removeAttribute("disabled");
        }
    }

    async function orchestrateCode() {
        const input = document.getElementById("doubt-message");
        const responseElement = document.getElementById("doubt-response");
        const submitButton = document.getElementById("code-orchestrate-submit");
        const language = document.getElementById("coding-language")?.value || null;
        const code = document.getElementById("coding-code")?.value.trim() || null;
        if (!input || !responseElement || !input.value.trim()) return;
        responseElement.textContent = "Orchestrating your coding request...";
        submitButton?.setAttribute("disabled", "disabled");
        try {
            const response = await apiFetch("/api/coach/code", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    message: input.value.trim(),
                    language,
                    code,
                }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Coding orchestration failed.");
            responseElement.textContent = `Intent: ${data.intent}\n\n${data.content}`;
        } catch (error) {
            responseElement.textContent = error.message || "Coding orchestrator unavailable.";
        } finally {
            submitButton?.removeAttribute("disabled");
        }
    }

function openDoubtPanel() {
    const panel = document.getElementById("doubt-panel");
    if (!panel) return;
    panel.hidden = false;
    document.body.classList.add("ai-panel-open");
    document.getElementById("doubt-message")?.focus();
}

function closeDoubtPanel() {
    const panel = document.getElementById("doubt-panel");
    if (!panel) return;
    panel.hidden = true;
    document.body.classList.remove("ai-panel-open");
}

    async function openPractice(subject = null) {
        const panel = document.getElementById("practice-panel");
        const questionElement = document.getElementById("practice-question");
        const progressElement = document.getElementById("practice-progress");
        if (!panel || !questionElement || !progressElement) return;

        panel.hidden = false;
        panel.scrollIntoView({behavior: "smooth", block: "start"});
        questionElement.textContent = "Loading practice questions...";
        try {
            const query = subject ? `?subject=${encodeURIComponent(subject)}&limit=100` : "?limit=100";
            const response = await apiFetch(`/api/practice/questions${query}`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Practice questions unavailable.");
            practiceQuestions = data.questions;
            practiceIndex = 0;
            renderPracticeQuestion();
        } catch (error) {
            questionElement.textContent = error.message || "Practice questions unavailable.";
            progressElement.textContent = "Unable to load the practice set.";
        }
    }

    function renderPracticeQuestion() {
        const question = practiceQuestions[practiceIndex];
        const questionElement = document.getElementById("practice-question");
        const progressElement = document.getElementById("practice-progress");
        const feedback = document.getElementById("practice-feedback");
        const nextButton = document.getElementById("next-practice");
        if (!question || !questionElement || !progressElement) return;

        progressElement.textContent = `Question ${practiceIndex + 1} of ${practiceQuestions.length} · ${question.subject} · ${question.difficulty}`;
        questionElement.innerHTML = `
            <h3>${question.prompt}</h3>
            <div class="practice-options">
                ${question.options.map((option, index) => `
                    <button type="button" class="practice-option" data-answer="${index}">${option}</button>
                `).join("")}
            </div>
        `;
        if (feedback) feedback.textContent = "";
        if (nextButton) nextButton.hidden = true;
        questionElement.querySelectorAll(".practice-option").forEach(button => {
            button.addEventListener("click", () => submitPracticeAnswer(Number(button.dataset.answer)));
        });
    }

    async function submitPracticeAnswer(answer) {
        const question = practiceQuestions[practiceIndex];
        const feedback = document.getElementById("practice-feedback");
        if (!question || !feedback) return;
        const options = document.querySelectorAll(".practice-option");
        options.forEach(option => { option.disabled = true; });
        try {
            const response = await apiFetch("/api/practice/answer", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({question_id: question.id, answer}),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Answer could not be checked.");
            feedback.textContent = `${data.correct ? "Correct ✓" : "Not quite."} ${data.explanation}`;
            if (!data.correct) {
                const correct = document.querySelector(`[data-answer="${data.correct_answer}"]`);
                correct?.classList.add("practice-correct");
            }
            document.getElementById("next-practice").hidden = false;
        } catch (error) {
            feedback.textContent = error.message || "Answer could not be checked.";
            options.forEach(option => { option.disabled = false; });
        }
    }

    function nextPracticeQuestion() {
        if (practiceIndex + 1 >= practiceQuestions.length) {
            const progressElement = document.getElementById("practice-progress");
            const questionElement = document.getElementById("practice-question");
            if (progressElement) progressElement.textContent = `Completed ${practiceQuestions.length} questions`;
            if (questionElement) questionElement.innerHTML = "<h3>Practice set complete 🎉</h3><p>Try another set after reviewing your Mistake Coach feedback.</p>";
            document.getElementById("next-practice").hidden = true;
            return;
        }
        practiceIndex += 1;
        renderPracticeQuestion();
    }
function csrfToken() {
    return getCookie("adhyan_csrf");
}


async function apiFetch(endpoint, options = {}) {

    const method = (
        options.method || "GET"
    ).toUpperCase();

    const headers = {
        ...(options.headers || {}),
    };

    if (
        method !== "GET" &&
        method !== "HEAD" &&
        method !== "OPTIONS"
    ) {
        const token = csrfToken();

        if (token) {
            headers["X-CSRF-Token"] = token;
        }

    }

    return fetch(
        `${API_URL}${endpoint}`,
        {
            ...options,
            headers,
            credentials: "include",
        }
    );
}


function setText(id, value) {

    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}


function showError(message) {

    console.error("Adhyan:", message);

    setText(
        "ai-recommendation",
        "Something went wrong"
    );

    setText(
        "ai-recommendation-text",
        message
    );
}


/* ============================================================
   AUTHENTICATED USER
   ============================================================ */

async function loadCurrentUser() {

    const response = await apiFetch("/auth/me");

    if (response.status === 401) {
        console.warn("User is not authenticated.");

        /*
         * Change this to your actual login page if needed.
         */
        window.location.href = "index.html";

        return null;
    }

    if (!response.ok) {
        throw new Error(
            `Unable to load user (${response.status})`
        );
    }

    const user = await response.json();

    currentUser = user;

    const name = user.name || "Student";

    document
        .querySelectorAll(".user-greeting")
        .forEach(element => {
            element.textContent =
                `Hi, ${name} 👋`;
        });

    const welcome = document.querySelector(
        ".welcome-section h1"
    );

    if (welcome) {
        welcome.textContent =
            `Good morning, ${name} 👋`;
    }

    return user;
}


/* ============================================================
   CURRENT STUDENT PROFILE
   ============================================================ */

async function loadStudentProfile() {

    const response = await apiFetch(
        "/api/students"
    );

    if (!response.ok) {
        throw new Error(
            `Unable to load student profile (${response.status})`
        );
    }

    const students = await response.json();

    if (!Array.isArray(students) || students.length === 0) {
        throw new Error(
            "No student profile is associated with this account."
        );
    }

    /*
     * For a trainee, the backend intentionally returns
     * only their own profile.
     */
    currentStudent = students[0];

    const name =
        currentStudent.name || "Student";

    document
        .querySelectorAll(".user-greeting")
        .forEach(element => {
            element.textContent =
                `Hi, ${name} 👋`;
        });

    const welcome = document.querySelector(
        ".welcome-section h1"
    );

    if (welcome) {
        welcome.textContent =
            `Good morning, ${name} 👋`;
    }

    updateStreak(
        currentStudent.current_streak
    );

    return currentStudent;
}


/* ============================================================
   DASHBOARD STATS
   ============================================================ */

async function loadDashboard() {

    const response = await apiFetch(
        "/dashboard"
    );

    if (!response.ok) {
        throw new Error(
            `Dashboard request failed (${response.status})`
        );
    }

    const data = await response.json();

    if (data.average_interest !== undefined) {
        setText(
            "interest-level",
            Number(
                data.average_interest
            ).toFixed(1)
        );
    }

    if (data.average_learning_depth !== undefined) {
        setText(
            "learning-depth",
            Number(
                data.average_learning_depth
            ).toFixed(1)
        );
    }

    return data;
}


/* ============================================================
   SUBJECTS
   ============================================================ */

async function loadSubjects() {

    const response = await apiFetch(
        "/api/subjects"
    );

    if (!response.ok) {
        throw new Error(
            `Unable to load subjects (${response.status})`
        );
    }

    currentSubjects = await response.json();

    return currentSubjects;
}


/* ============================================================
   PROGRESS
   ============================================================ */

async function loadProgress() {

    if (!currentStudent) {
        throw new Error(
            "Student profile is not loaded."
        );
    }

    const response = await apiFetch(
        `/api/students/${currentStudent.id}/progress`
    );

    if (!response.ok) {
        throw new Error(
            `Unable to load progress (${response.status})`
        );
    }

    currentProgress = await response.json();

    renderProgress();

    return currentProgress;
}


/* ============================================================
   RENDER SUBJECT PROGRESS
   ============================================================ */

function renderProgress() {

    /*
     * Find the first main feature card.
     * This is the Subjects card in your current HTML.
     */
    const cards = document.querySelectorAll(
        ".main-features .feature-card"
    );

    if (!cards.length) {
        return;
    }

    const subjectsCard = cards[0];

    /*
     * Preserve:
     * icon
     * LEARNING label
     * Subjects heading
     */
    const icon = subjectsCard.querySelector(
        ".feature-icon"
    );

    const label = subjectsCard.querySelector(
        ".stat-label"
    );

    const heading = subjectsCard.querySelector(
        "h3"
    );

    subjectsCard.replaceChildren();

    if (icon) {
        subjectsCard.appendChild(icon);
    }

    if (label) {
        subjectsCard.appendChild(label);
    }

    if (heading) {
        subjectsCard.appendChild(heading);
    }

    if (
        !currentSubjects ||
        currentSubjects.length === 0
    ) {

        const empty = document.createElement("p");

        empty.textContent =
            "No subjects have been added yet.";

        subjectsCard.appendChild(empty);

        return;
    }


    currentSubjects.forEach(subject => {

        const progressRecord =
            currentProgress.find(
                item =>
                    item.subject_id === subject.id
            );

        const percentage =
            progressRecord
                ? Number(
                    progressRecord.progress || 0
                )
                : 0;

        const row =
            document.createElement("div");

        row.className =
            "subject-row";


        const name =
            document.createElement("span");

        name.textContent =
            subject.name;


        const percentageText =
            document.createElement("span");

        percentageText.textContent =
            `${Math.round(
                Math.max(
                    0,
                    Math.min(
                        100,
                        percentage
                    )
                )
            )}%`;


        row.append(
            name,
            percentageText
        );


        const progressContainer =
            document.createElement("div");

        progressContainer.className =
            "mini-progress";


        const progressBar =
            document.createElement("div");

        progressBar.style.width =
            `${Math.max(
                0,
                Math.min(
                    100,
                    percentage
                )
            )}%`;


        progressContainer.appendChild(
            progressBar
        );


        subjectsCard.append(
            row,
            progressContainer
        );
    });
}


/* ============================================================
   SKILLS
   ============================================================ */

function renderSkills() {

    const cards = document.querySelectorAll(
        ".quick-stats .stat-card"
    );

    if (!cards.length) {
        return;
    }

    const skillsCard = cards[0];

    const rows = skillsCard.querySelectorAll(
        ".skill-row"
    );

    /*
     * We don't have a skills API yet.
     *
     * Therefore we remove fake Gold/Silver/Bronze
     * values rather than pretending they're real.
     */
    rows.forEach(row => {

        const skillName =
            row.querySelector("span");

        const skillValue =
            row.querySelector("strong");

        if (!skillName || !skillValue) {
            return;
        }

        const matchingProgress =
            currentProgress.find(
                progress => {

                    if (!progress.subject_name) {
                        return false;
                    }

                    return (
                        progress.subject_name
                            .toLowerCase()
                            .includes(
                                skillName.textContent
                                    .toLowerCase()
                            )
                    );
                }
            );

        if (matchingProgress) {

            skillValue.textContent =
                `${Math.round(
                    matchingProgress.progress || 0
                )}%`;

        } else {

            skillValue.textContent =
                "Not started";
        }
    });
}


/* ============================================================
   STREAK
   ============================================================ */

function updateStreak(streak) {

    const button =
        document.querySelector(
            ".streak-btn"
        );

    if (!button) {
        return;
    }

    button.textContent =
        `🔥 ${Number(streak || 0)}`;
}


/* ============================================================
   STUDENTS / COLLABORATION
   ============================================================ */

async function loadStudents() {

    const count =
        document.getElementById(
            "student-count"
        );

    const topic =
        document.getElementById(
            "student-topic"
        );

    const list =
        document.getElementById(
            "student-list"
        );

    if (count) {
        count.textContent =
            "Loading...";
    }

    if (topic) {
        topic.textContent =
            "Checking available learners...";
    }

    if (list) {
        list.textContent =
            "Loading students...";
    }

    try {

        const response = await apiFetch(
            "/api/students"
        );

        if (!response.ok) {
            throw new Error(
                `Student request failed (${response.status})`
            );
        }

        const students =
            await response.json();

        /*
         * IMPORTANT:
         *
         * For TRAINEE accounts your backend intentionally
         * returns only the current student's profile.
         *
         * Therefore this does NOT pretend that other
         * students are available.
         */
        displayStudents(students);

        return students;

    } catch (error) {

        console.error(
            "Student loading error:",
            error
        );

        if (count) {
            count.textContent =
                "Unavailable";
        }

        if (topic) {
            topic.textContent =
                "Could not connect to the student service.";
        }

        if (list) {
            list.textContent =
                "Please try again.";
        }

        return [];
    }
}


function displayStudents(students) {

    const list =
        document.getElementById(
            "student-list"
        );

    const count =
        document.getElementById(
            "student-count"
        );

    const topic =
        document.getElementById(
            "student-topic"
        );

    if (!list) {
        return;
    }

    list.replaceChildren();

    if (
        !Array.isArray(students) ||
        students.length === 0
    ) {

        if (count) {
            count.textContent =
                "No students available";
        }

        if (topic) {
            topic.textContent =
                "No student profile found.";
        }

        list.textContent =
            "No learners found.";

        return;
    }


    if (count) {

        count.textContent =
            `${students.length} profile${
                students.length === 1
                    ? ""
                    : "s"
            } loaded`;
    }


    if (topic) {

        topic.textContent =
            "Connected to Adhyan student service";
    }


    students
        .slice(0, 5)
        .forEach(student => {

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "activity-row";


            const icon =
                document.createElement(
                    "span"
                );

            icon.textContent =
                "👤";


            const info =
                document.createElement(
                    "div"
                );


            const name =
                document.createElement(
                    "strong"
                );

            name.textContent =
                student.name ||
                "Student";


            const details =
                document.createElement(
                    "small"
                );

            details.textContent =
                student.course ||
                "Adhyan learner";


            info.append(
                name,
                details
            );

            row.append(
                icon,
                info
            );

            list.appendChild(
                row
            );
        });
}


/* ============================================================
   ADAPTIVE ENGINE
   ============================================================ */

function renderRLTrace(data) {
    const state = data.state || [];
    const actions = ["EXPLAIN", "HINT", "REVISION", "CHALLENGE", "PRACTICE", "SIMPLIFY"];
    const stateElement = document.getElementById("rl-state");
    const valuesElement = document.getElementById("q-values");
    if (!stateElement || !valuesElement) return;

    stateElement.innerHTML = ["Accuracy", "Attempts", "Time", "Mastery"]
        .map((label, index) => `<span>${label} ${(Number(state[index] || 0) * 100).toFixed(0)}%</span>`)
        .join("");

    const values = data.q_values || [];
    const maximum = Math.max(...values.map(value => Math.abs(Number(value))), 0.01);
    valuesElement.innerHTML = actions.map((action, index) => {
        const value = Number(values[index] || 0);
        const width = Math.max(5, Math.round(Math.abs(value) / maximum * 100));
        const selected = index === data.action_index ? " selected" : "";
        return `<div class="q-value${selected}"><span>${action}</span><i><b style="width:${width}%"></b></i><em>${value.toFixed(3)}</em></div>`;
    }).join("");
    setText("rl-selected-action", `Policy chose ${data.action || "--"}`);
}

async function loadAIRecommendation() {

    setText(
        "ai-recommendation",
        "Analyzing your learning progress..."
    );

    setText(
        "ai-recommendation-text",
        "Adhyan is selecting your next learning step."
    );

    setText(
        "ai-subject",
        "--"
    );

    setText(
        "ai-difficulty",
        "--"
    );

    setText(
        "ai-status",
        "Connecting..."
    );


    try {

        const response =
            await apiFetch(
                "/api/recommend",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",
                    },

                    body: JSON.stringify({}),
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                `Recommendation failed (${response.status})`
            );
        }


        currentRecommendation =
            data;

        renderRLTrace(data);


        setText(
            "ai-recommendation",
            formatAction(
                data.action
            )
        );


        setText(
            "ai-recommendation-text",
            data.content ||
            `Adhyan recommends ${
                String(
                    data.action || ""
                ).toLowerCase()
            } for ${
                data.topic || "your current subject"
            }.`
        );


        setText(
            "ai-subject",
            data.subject?.name ||
            data.subject ||
            "--"
        );


        setText(
            "ai-difficulty",
            data.difficulty ||
            "--"
        );


        setText(
            "ai-status",
            data.llm_available
                ? "DQN + LLM"
                : "DQN active"
        );

        renderSessionChunk();
        setText(
            "ai-explanation",
            data.explanation?.summary ||
            "The DQN selected the action with the highest predicted learning value."
        );
        configureAdaptiveFocus();


        return data;

    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );


        setText(
            "ai-recommendation",
            "Adaptive Engine unavailable"
        );


        setText(
            "ai-recommendation-text",
            error.message ||
            "Unable to generate a recommendation."
        );


        setText(
            "ai-status",
            "Unavailable"
        );


        return null;
    }
}


/* ============================================================
   ACTION FORMATTER
   ============================================================ */

function formatAction(action) {

    if (!action) {
        return "Recommended Learning Step";
    }

    return String(action)
        .toLowerCase()
        .replace(
            /\b\w/g,
            letter =>
                letter.toUpperCase()
        );
}


/* ============================================================
   START RECOMMENDED SESSION
   ============================================================ */

function startRecommendedSession() {

    if (!currentRecommendation) {

        loadAIRecommendation().then(() => {
            if (currentRecommendation) startRecommendedSession();
        });

        return;
    }


    const title =
        document.getElementById(
            "ai-recommendation"
        );

    const description =
        document.getElementById(
            "ai-recommendation-text"
        );

    const button =
        document.getElementById(
            "start-ai-session"
        );


    if (title) {

        title.textContent =
            `${formatAction(
                currentRecommendation.action
            )} Session`;
    }


    if (description) {

        description.textContent =
            currentRecommendation.content ||
            "Your recommended activity is ready.";
    }


    if (button) {

        button.textContent =
            "Session Active ✓";

        button.disabled = true;
    }

    renderSessionChunk();
    configureAdaptiveFocus();
    if (!focusTimer) toggleFocusTimer();
    document.getElementById("smart-session")?.scrollIntoView({
        behavior: "smooth",
        block: "center",
    });
}


/* ============================================================
   REFRESH EVERYTHING
   ============================================================ */

async function refreshDashboard() {

    const button =
        document.getElementById(
            "refresh-dashboard"
        );

    if (button) {
        button.disabled = true;
        button.textContent =
            "Refreshing...";
    }


    try {

        await loadStudentProfile();

        await Promise.all([
            loadDashboard(),
            loadSubjects(),
            loadProgress(),
        ]);

        renderSkills();

    } catch (error) {

        console.error(
            "Dashboard refresh error:",
            error
        );

        showError(
            error.message ||
            "Unable to refresh dashboard."
        );

    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "Refresh Data →";
        }
    }
}


/* ============================================================
   NAVIGATION BUTTONS
   ============================================================ */

function initializeNavigation() {

    const navButtons =
        document.querySelectorAll(
            ".nav-button"
        );

    navButtons.forEach(button => {

        const text =
            button
                .querySelector("span")
                ?.textContent
                ?.trim()
                ?.toLowerCase();


        button.addEventListener(
            "click",
            () => {

                if (text === "home") {

                    window.scrollTo({
                        top: 0,
                        behavior: "smooth",
                    });

                } else if (text === "tests") {
                    openPractice();
                }
            }
        );
    });
}


/* ============================================================
   SLIDER
   ============================================================ */

function initializeSlider() {

    const slides =
        document.querySelectorAll(
            ".promo-slide"
        );

    const dots =
        document.querySelectorAll(
            ".dot"
        );

    if (!slides.length) {
        return;
    }

    let currentSlide = 0;


    function showSlide(index) {

        slides.forEach(
            (slide, i) => {

                slide.classList.toggle(
                    "active",
                    i === index
                );
            }
        );


        dots.forEach(
            (dot, i) => {

                dot.classList.toggle(
                    "active",
                    i === index
                );
            }
        );
    }


    dots.forEach(
        (dot, index) => {

            dot.addEventListener(
                "click",
                () => {

                    currentSlide =
                        index;

                    showSlide(
                        currentSlide
                    );
                }
            );
        }
    );


    setInterval(
        () => {

            currentSlide =
                (
                    currentSlide + 1
                ) % slides.length;

            showSlide(
                currentSlide
            );

        },
        5000
    );
}


/* ============================================================
   BUTTONS
   ============================================================ */

function initializeButtons() {
    document.getElementById("open-doubt-panel")?.addEventListener("click", openDoubtPanel);
    document.getElementById("close-doubt-panel")?.addEventListener("click", closeDoubtPanel);
    document.getElementById("doubt-panel")?.addEventListener("click", (event) => {
        if (event.target.id === "doubt-panel") closeDoubtPanel();
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeDoubtPanel();
    });
    document.querySelectorAll(".sample-prompt").forEach((button) => {
        button.addEventListener("click", () => {
            const input = document.getElementById("doubt-message");
            if (!input) return;
            input.value = button.dataset.prompt || "";
            input.focus();
        });
    });
    document.getElementById("coach-form")?.addEventListener("submit", analyzeMistake);
    document.getElementById("doubt-form")?.addEventListener("submit", askLearningQuestion);
    document.getElementById("code-orchestrate-submit")?.addEventListener("click", orchestrateCode);

    const startButton =
        document.getElementById(
            "start-ai-session"
        );

    if (startButton) {

        startButton.addEventListener(
            "click",
            startRecommendedSession
        );
    }


    const refreshDashboardButton =
        document.getElementById(
            "refresh-dashboard"
        );

    if (refreshDashboardButton) {

        refreshDashboardButton.addEventListener(
            "click",
            refreshDashboard
        );
    }


    const refreshStudents =
        document.getElementById(
            "refresh-students"
        );

    if (refreshStudents) {

        refreshStudents.addEventListener(
            "click",
            async () => {

                refreshStudents.disabled =
                    true;

                refreshStudents.textContent =
                    "Loading...";

                await loadStudents();

                refreshStudents.disabled =
                    false;

                refreshStudents.textContent =
                    "Find a Study Room →";
            }
        );
    }

    const focusLength = document.getElementById("focus-length");
    const focusButton = document.getElementById("focus-timer-button");
    const stopFocusButton = document.getElementById("stop-focus-button");
    focusLength?.addEventListener("change", configureAdaptiveFocus);
    focusButton?.addEventListener("click", toggleFocusTimer);
    stopFocusButton?.addEventListener("click", stopFocusSession);
    document.getElementById("open-practice")?.addEventListener("click", () => openPractice());
    document.getElementById("close-practice")?.addEventListener("click", () => {
        document.getElementById("practice-panel").hidden = true;
    });
    document.getElementById("next-practice")?.addEventListener("click", nextPracticeQuestion);
    document.getElementById("continue-learning")?.addEventListener("click", () => {
        document.getElementById("start-ai-session")?.click();
    });
    document.getElementById("explore-adaptive")?.addEventListener("click", () => {
        document.getElementById("ai-recommendation")?.scrollIntoView({behavior: "smooth"});
    });
    document.getElementById("promo-focus")?.addEventListener("click", () => {
        document.getElementById("focus-timer-button")?.click();
    });
    document.getElementById("promo-study-room")?.addEventListener("click", () => {
        document.getElementById("refresh-students")?.click();
    });
}


/* ============================================================
   LOGOUT
   ============================================================ */

async function logout() {

    try {

        const response =
            await apiFetch(
                "/auth/logout",
                {
                    method: "POST",
                }
            );


        if (!response.ok) {

            const data =
                await response.json()
                    .catch(() => ({}));

            throw new Error(
                data.detail ||
                "Logout failed."
            );
        }


        window.location.href =
            "index.html";

    } catch (error) {

        console.error(
            "Logout error:",
            error
        );

        alert(
            "Unable to logout right now."
        );
    }
}


/* ============================================================
   PROFILE / LOGOUT BUTTON
   ============================================================ */

function initializeUserActions() {

    const profileButton =
        document.querySelector(
            ".profile-btn"
        );

    if (profileButton) {

        profileButton.addEventListener(
            "click",
            () => {

                alert(
                    currentStudent
                        ? `Logged in as ${currentStudent.name}`
                        : "Profile information unavailable."
                );
            }
        );
    }


}


/* ============================================================
   INITIALIZATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        initializeSlider();

        initializeButtons();

        initializeNavigation();

        initializeUserActions();


        try {

            /*
             * Authentication first.
             */
            await loadCurrentUser();


            /*
             * Load the actual student profile.
             */
            await loadStudentProfile();


            /*
             * Load independent dashboard data
             * in parallel.
             */
            await Promise.all([
                loadDashboard(),
                loadSubjects(),
                loadProgress(),
            ]);


            /*
             * Replace fake skill values with
             * database-backed progress where possible.
             */
            renderSkills();


            /*
             * Load the adaptive recommendation last.
             */
            await loadAIRecommendation();


            /*
             * Load collaboration information.
             */
            await loadStudents();


            console.log(
                "Adhyan dashboard initialized successfully."
            );

        } catch (error) {

            console.error(
                "Dashboard initialization failed:",
                error
            );

            showError(
                error.message ||
                "Unable to initialize dashboard."
            );
        }
    }
);