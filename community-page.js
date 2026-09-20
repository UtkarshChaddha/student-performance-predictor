"use strict";

const COMMUNITY_PAGE_API = window.ADHYAN_API_URL || (window.location.hostname === "localhost" ? "http://localhost:8000" : "http://127.0.0.1:8000");
let pagePosts = [];

function pageCsrf() {
    const match = document.cookie.match(/(?:^|; )adhyan_csrf=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
}

function pageEscape(value) {
    return String(value).replace(/[&<>\"']/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[character]));
}

function pageAge(value) {
    const minutes = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 60000));
    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes} min ago`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)} hr ago`;
    return `${Math.floor(minutes / 1440)} days ago`;
}

async function pageRequest(path, options = {}) {
    const isWrite = options.method && options.method !== "GET";
    if (isWrite && !pageCsrf()) throw new Error("Your session has expired. Please sign in again.");
    const response = await fetch(`${COMMUNITY_PAGE_API}${path}`, {
        credentials: "include",
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(isWrite ? {"X-CSRF-Token": pageCsrf()} : {}),
            ...(options.headers || {}),
        },
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || "Community is temporarily unavailable.");
    return data;
}

function renderPageFeed() {
    const feed = document.getElementById("page-feed");
    const query = document.getElementById("page-search").value.trim().toLowerCase();
    const filter = document.getElementById("page-filter").value;
    const visible = pagePosts.filter(post =>
        (filter === "all" || post.topic === filter) &&
        (!query || `${post.author} ${post.content} ${post.topic}`.toLowerCase().includes(query))
    );
    if (!visible.length) {
        feed.innerHTML = '<div class="empty-page">No conversations match your search yet.<br><button class="retry-page" id="page-retry">Refresh feed</button></div>';
        return;
    }
    feed.innerHTML = visible.map(post => `
        <article class="post-card" id="page-post-${post.id}">
            <div class="large-avatar">${pageEscape(post.initials)}</div>
            <div class="post-card-content">
                <div class="post-head"><div><strong>${pageEscape(post.author)}</strong><time>${pageAge(post.created_at)}</time></div><span class="post-topic">${pageEscape(post.topic === "win" ? "SMALL WIN" : post.topic.toUpperCase())}</span></div>
                <div class="post-body">${pageEscape(post.content)}</div>
                <div class="post-actions"><button class="post-action ${post.liked ? "liked" : ""}" data-page-action="like" data-id="${post.id}">${post.liked ? "♥" : "♡"} ${post.likes}</button><button class="post-action" data-page-action="comments" data-id="${post.id}">◯ ${post.comments.length} ${post.comments.length === 1 ? "reply" : "replies"}</button><button class="post-action" data-page-action="share" data-id="${post.id}">↗ Share</button></div>
                <div class="post-comments" id="page-comments-${post.id}" hidden>${post.comments.map(comment => `<div class="post-comment"><b>${pageEscape(comment.author)}</b>${pageEscape(comment.content)}</div>`).join("")}<form class="reply-form" data-post-id="${post.id}"><input name="content" maxlength="180" required placeholder="Add a reply..."><button>Reply</button></form></div>
            </div>
        </article>`).join("");
}

async function loadPageFeed() {
    const feed = document.getElementById("page-feed");
    feed.innerHTML = '<div class="empty-page">Loading your learning network...</div>';
    try {
        pagePosts = await pageRequest("/api/community/posts");
        renderPageFeed();
    } catch (error) {
        feed.innerHTML = `<div class="empty-page"><strong>${pageEscape(error.message)}</strong><br><button class="retry-page" id="page-retry">Try again</button></div>`;
    }
}

function showPageToast(message) {
    const toast = document.getElementById("page-toast");
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2200);
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("page-post-form");
    const content = document.getElementById("page-post-content");
    const submit = document.getElementById("page-post-submit");
    content.addEventListener("input", () => { submit.disabled = !content.value.trim(); });
    form.addEventListener("submit", async event => {
        event.preventDefault();
        submit.disabled = true;
        try {
            await pageRequest("/api/community/posts", {method: "POST", body: JSON.stringify({content: content.value.trim(), topic: document.getElementById("page-post-topic").value})});
            content.value = "";
            await loadPageFeed();
            showPageToast("Your post is live.");
        } catch (error) { showPageToast(error.message); }
        submit.disabled = !content.value.trim();
    });
    document.getElementById("page-search").addEventListener("input", renderPageFeed);
    document.getElementById("page-filter").addEventListener("change", renderPageFeed);
    document.getElementById("page-feed").addEventListener("click", async event => {
        if (event.target.id === "page-retry") return loadPageFeed();
        const button = event.target.closest("[data-page-action]");
        if (!button) return;
        const id = button.dataset.id;
        if (button.dataset.pageAction === "comments") {
            document.getElementById(`page-comments-${id}`).toggleAttribute("hidden");
            return;
        }
        if (button.dataset.pageAction === "share") {
            await navigator.clipboard?.writeText(`${location.href}#page-post-${id}`);
            showPageToast("Post link copied.");
            return;
        }
        try {
            const updated = await pageRequest(`/api/community/posts/${id}/like`, {method: "POST"});
            pagePosts = pagePosts.map(post => post.id === updated.id ? updated : post);
            renderPageFeed();
        } catch (error) { showPageToast(error.message); }
    });
    document.getElementById("page-feed").addEventListener("submit", async event => {
        if (!event.target.matches(".reply-form")) return;
        event.preventDefault();
        const input = event.target.elements.content;
        try {
            const updated = await pageRequest(`/api/community/posts/${event.target.dataset.postId}/comments`, {method: "POST", body: JSON.stringify({content: input.value.trim()})});
            pagePosts = pagePosts.map(post => post.id === updated.id ? updated : post);
            renderPageFeed();
        } catch (error) { showPageToast(error.message); }
    });
    loadPageFeed();
});
