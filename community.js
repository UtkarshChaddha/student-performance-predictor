"use strict";

const COMMUNITY_API = window.ADHYAN_API_URL || (window.location.hostname === "localhost" ? "http://localhost:8000" : "http://127.0.0.1:8000");
let communityPosts = [];

function communityCsrf() {
    const match = document.cookie.match(/(?:^|; )adhyan_csrf=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
}

function communityEscape(value) {
    return String(value).replace(/[&<>\"']/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[character]));
}

function communityTime(value) {
    const age = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 60000));
    if (age < 1) return "Just now";
    if (age < 60) return `${age} min ago`;
    if (age < 1440) return `${Math.floor(age / 60)} hr ago`;
    return `${Math.floor(age / 1440)} days ago`;
}

async function communityRequest(path, options = {}) {
    const isWrite = options.method && options.method !== "GET";
    if (isWrite && !communityCsrf()) {
        throw new Error("Your session has expired. Please sign in again.");
    }
    const response = await fetch(`${COMMUNITY_API}${path}`, {
        credentials: "include",
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.method && options.method !== "GET" ? {"X-CSRF-Token": communityCsrf()} : {}),
            ...(options.headers || {}),
        },
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || "Community service is unavailable.");
    return data;
}

function renderCommunity() {
    const feed = document.getElementById("community-feed");
    if (!feed) return;
    const query = document.getElementById("community-search")?.value.trim().toLowerCase() || "";
    const filter = document.getElementById("community-filter")?.value || "all";
    const posts = communityPosts.filter(post =>
        (filter === "all" || post.topic === filter) &&
        (!query || `${post.author} ${post.content} ${post.topic}`.toLowerCase().includes(query))
    );
    if (!posts.length) {
        feed.innerHTML = '<div class="community-empty">No posts match that filter yet. Start the conversation.</div>';
        return;
    }
    feed.innerHTML = posts.map(post => `
        <article class="community-post">
            <div class="community-post-avatar">${communityEscape(post.initials)}</div>
            <div class="community-post-content">
                <div class="community-post-meta">
                    <div><strong>${communityEscape(post.author)}</strong><time>${communityTime(post.created_at)}</time></div>
                    <span class="community-tag">${communityEscape(post.topic.replace("win", "SMALL WIN").toUpperCase())}</span>
                </div>
                <div class="community-post-body">${communityEscape(post.content)}</div>
                <div class="community-actions">
                    <button class="community-action ${post.liked ? "liked" : ""}" data-action="like" data-id="${post.id}">${post.liked ? "♥" : "♡"} ${post.likes}</button>
                    <button class="community-action" data-action="comments" data-id="${post.id}">◯ ${post.comments.length} ${post.comments.length === 1 ? "reply" : "replies"}</button>
                    <button class="community-action" data-action="share" data-id="${post.id}">↗ Share</button>
                </div>
                <div class="community-comments" id="community-comments-${post.id}" hidden>
                    ${post.comments.map(comment => `<div class="community-comment"><strong>${communityEscape(comment.author)}</strong>${communityEscape(comment.content)}</div>`).join("")}
                    <form class="comment-form" data-post-id="${post.id}"><input name="content" maxlength="180" required placeholder="Add a thoughtful reply..."><button type="submit">Reply</button></form>
                </div>
            </div>
        </article>`).join("");
}

async function loadCommunity() {
    try {
        communityPosts = await communityRequest("/api/community/posts");
        renderCommunity();
    } catch (error) {
        const feed = document.getElementById("community-feed");
        if (feed) feed.innerHTML = `<div class="community-empty"><strong>${communityEscape(error.message)}</strong><button class="community-retry" type="button" id="community-retry">Try again</button></div>`;
    }
}

function showCommunityMessage(message) {
    const feed = document.getElementById("community-feed");
    if (!feed) return;
    const notice = document.createElement("div");
    notice.className = "community-empty";
    notice.textContent = message;
    feed.prepend(notice);
    setTimeout(() => notice.remove(), 2600);
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("community-form");
    const content = document.getElementById("community-content");
    const submit = document.getElementById("community-submit");
    const topic = document.getElementById("community-topic");
    content?.addEventListener("input", () => { submit.disabled = !content.value.trim(); });
    form?.addEventListener("submit", async event => {
        event.preventDefault();
        submit.disabled = true;
        try {
            await communityRequest("/api/community/posts", {method: "POST", body: JSON.stringify({content: content.value.trim(), topic: topic.value})});
            content.value = "";
            await loadCommunity();
            showCommunityMessage("Your post is live in the community.");
        } catch (error) {
            showCommunityMessage(error.message);
        } finally {
            submit.disabled = !content.value.trim();
        }
    });
    document.getElementById("community-search")?.addEventListener("input", renderCommunity);
    document.getElementById("community-filter")?.addEventListener("change", renderCommunity);
    document.getElementById("community-refresh")?.addEventListener("click", loadCommunity);
    document.getElementById("community-feed")?.addEventListener("click", event => {
        if (event.target.id === "community-retry") loadCommunity();
    });
    document.getElementById("community-feed")?.addEventListener("click", async event => {
        const button = event.target.closest("[data-action]");
        if (!button) return;
        const id = button.dataset.id;
        if (button.dataset.action === "comments") {
            document.getElementById(`community-comments-${id}`)?.toggleAttribute("hidden");
            return;
        }
        if (button.dataset.action === "share") {
            await navigator.clipboard?.writeText(`${location.href}#community-post-${id}`);
            showCommunityMessage("Post link copied.");
            return;
        }
        try {
            const updated = await communityRequest(`/api/community/posts/${id}/like`, {method: "POST"});
            communityPosts = communityPosts.map(post => post.id === updated.id ? updated : post);
            renderCommunity();
        } catch (error) { showCommunityMessage(error.message); }
    });
    document.getElementById("community-feed")?.addEventListener("submit", async event => {
        if (!event.target.matches(".comment-form")) return;
        event.preventDefault();
        const input = event.target.elements.content;
        try {
            const updated = await communityRequest(`/api/community/posts/${event.target.dataset.postId}/comments`, {method: "POST", body: JSON.stringify({content: input.value.trim()})});
            communityPosts = communityPosts.map(post => post.id === updated.id ? updated : post);
            renderCommunity();
        } catch (error) { showCommunityMessage(error.message); }
    });
    loadCommunity();
});
