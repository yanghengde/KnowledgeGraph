(() => {
    "use strict";

    const $ = (selector) => document.querySelector(selector);
    const elements = {
        sidebar: $("#qaSidebar"),
        sessionList: $("#sessionList"),
        sessionCount: $("#sessionCount"),
        sessionSearch: $("#sessionSearch"),
        title: $("#conversationTitle"),
        stage: $("#messageStage"),
        welcome: $("#welcomePanel"),
        messages: $("#messageList"),
        input: $("#questionInput"),
        send: $("#sendButton"),
        status: $("#streamStatus"),
        statusText: $("#streamStatusText"),
        connectionDot: $("#connectionDot"),
        connectionLabel: $("#connectionLabel"),
        connectionDetail: $("#connectionDetail"),
        toast: $("#toast"),
    };

    const state = {
        sessions: [],
        current: null,
        streaming: false,
        abortController: null,
        search: "",
    };

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
        })[char]);
    }

    function renderInline(value) {
        return escapeHtml(value)
            .replace(/`([^`]+)`/g, "<code>$1</code>")
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    }

    function renderMarkdown(value) {
        const source = String(value || "").replace(/\r\n/g, "\n");
        const codeBlocks = [];
        let text = source.replace(/```([\w-]*)\n([\s\S]*?)```/g, (_, language, code) => {
            const index = codeBlocks.length;
            codeBlocks.push(`<div class="code-block"><div class="code-header"><span>${escapeHtml(language || "text")}</span><button type="button" class="copy-code">复制</button></div><pre>${escapeHtml(code.trim())}</pre></div>`);
            return `\n@@CODEBLOCK_${index}@@\n`;
        });
        const lines = text.split("\n");
        const output = [];
        let listType = null;
        const closeList = () => {
            if (listType) output.push(`</${listType}>`);
            listType = null;
        };
        for (const line of lines) {
            const codeMatch = line.match(/^@@CODEBLOCK_(\d+)@@$/);
            if (codeMatch) {
                closeList();
                output.push(codeBlocks[Number(codeMatch[1])]);
                continue;
            }
            const heading = line.match(/^(#{2,3})\s+(.+)$/);
            if (heading) {
                closeList();
                const level = heading[1].length;
                output.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
                continue;
            }
            const unordered = line.match(/^[-*]\s+(.+)$/);
            const ordered = line.match(/^\d+\.\s+(.+)$/);
            if (unordered || ordered) {
                const nextType = unordered ? "ul" : "ol";
                if (listType !== nextType) {
                    closeList();
                    output.push(`<${nextType}>`);
                    listType = nextType;
                }
                output.push(`<li>${renderInline((unordered || ordered)[1])}</li>`);
                continue;
            }
            closeList();
            if (line.trim()) output.push(`<p>${renderInline(line)}</p>`);
        }
        closeList();
        return output.join("");
    }

    function showToast(message) {
        elements.toast.textContent = message;
        elements.toast.classList.add("visible");
        window.clearTimeout(showToast.timer);
        showToast.timer = window.setTimeout(() => elements.toast.classList.remove("visible"), 1600);
    }

    function formatTime(value) {
        if (!value) return "";
        const date = new Date(value);
        const now = new Date();
        const sameDay = date.toDateString() === now.toDateString();
        return sameDay
            ? date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
            : date.toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" });
    }

    function renderSessions() {
        const term = state.search.trim().toLowerCase();
        const sessions = state.sessions.filter((item) => !term || `${item.title} ${item.preview}`.toLowerCase().includes(term));
        elements.sessionCount.textContent = String(state.sessions.length);
        if (!sessions.length) {
            elements.sessionList.innerHTML = `<div class="session-empty">${term ? "没有匹配的历史会话" : "还没有问答记录。发送第一个制造问题后，会话将保存在这里。"}</div>`;
            return;
        }
        elements.sessionList.innerHTML = sessions.map((item) => `
            <div class="session-item ${state.current?.id === item.id ? "active" : ""}" data-session-id="${escapeHtml(item.id)}" role="button" tabindex="0">
                <div class="session-copy"><strong>${escapeHtml(item.title || "制造知识问答")}</strong><small>${escapeHtml(formatTime(item.updated_at))} · ${Math.ceil((item.message_count || 0) / 2)} 轮</small></div>
                <button class="session-delete" type="button" data-delete-session="${escapeHtml(item.id)}" title="删除会话" aria-label="删除会话">×</button>
            </div>
        `).join("");
    }

    async function fetchJson(url, options = {}) {
        const response = await fetch(url, options);
        if (!response.ok) {
            let detail = `请求失败（HTTP ${response.status}）`;
            try {
                const body = await response.json();
                detail = body.detail || body.error || detail;
            } catch (_) {}
            throw new Error(detail);
        }
        return response.json();
    }

    async function refreshSessions() {
        const payload = await fetchJson("/api/manufacturing-chat/sessions?limit=200");
        state.sessions = payload.items || [];
        renderSessions();
    }

    function setCurrentSession(session) {
        state.current = session;
        if (session) localStorage.setItem("manufacturing_qa_session_id", session.id);
        elements.title.textContent = session?.title || "制造知识问答";
        elements.messages.innerHTML = "";
        const messages = session?.messages || [];
        elements.welcome.hidden = messages.length > 0;
        for (const message of messages) appendMessage(message.role, message.content || "", false);
        renderSessions();
        window.requestAnimationFrame(() => { elements.stage.scrollTop = elements.stage.scrollHeight; });
    }

    async function loadSession(sessionId) {
        if (state.streaming) return;
        try {
            const session = await fetchJson(`/api/manufacturing-chat/sessions/${encodeURIComponent(sessionId)}`);
            setCurrentSession(session);
            closeMobileSidebar();
        } catch (error) {
            showToast(error.message);
            await refreshSessions();
        }
    }

    async function createSession() {
        const session = await fetchJson("/api/manufacturing-chat/sessions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: "新建制造问答" }),
        });
        state.sessions.unshift({ ...session, message_count: 0, preview: "" });
        setCurrentSession(session);
        elements.input.focus();
        closeMobileSidebar();
        return session;
    }

    async function deleteSession(sessionId) {
        if (!sessionId || state.streaming) return;
        await fetchJson(`/api/manufacturing-chat/sessions/${encodeURIComponent(sessionId)}`, { method: "DELETE" });
        state.sessions = state.sessions.filter((item) => item.id !== sessionId);
        if (state.current?.id === sessionId) {
            state.current = null;
            localStorage.removeItem("manufacturing_qa_session_id");
            setCurrentSession(null);
        }
        renderSessions();
        showToast("会话已删除");
    }

    function appendMessage(role, content, animate = true) {
        elements.welcome.hidden = true;
        const article = document.createElement("article");
        article.className = `message ${role}`;
        if (!animate) article.style.animation = "none";
        article.innerHTML = `
            <div class="message-avatar">${role === "assistant" ? "MG" : "我"}</div>
            <div class="message-body">
                <div class="message-label">${role === "assistant" ? "制造知识助手" : "您"}</div>
                <div class="message-content">${renderMarkdown(content)}</div>
                <div class="message-actions"><button type="button" class="message-action copy-message">复制回答</button></div>
            </div>
        `;
        if (role === "user") article.querySelector(".message-actions").remove();
        elements.messages.appendChild(article);
        elements.stage.scrollTop = elements.stage.scrollHeight;
        return article;
    }

    function updateComposer() {
        elements.input.style.height = "auto";
        elements.input.style.height = `${Math.min(elements.input.scrollHeight, 180)}px`;
        elements.send.disabled = !state.streaming && !elements.input.value.trim();
    }

    function setStreaming(value) {
        state.streaming = value;
        elements.input.disabled = value;
        elements.status.hidden = !value;
        elements.send.disabled = false;
        elements.send.classList.toggle("stop", value);
        elements.send.innerHTML = value
            ? `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="1" fill="currentColor" stroke="none"/></svg>`
            : `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6"/></svg>`;
        elements.send.setAttribute("aria-label", value ? "停止生成" : "发送问题");
        if (!value) updateComposer();
    }

    async function sendQuestion(questionOverride = null) {
        if (state.streaming) {
            state.abortController?.abort();
            return;
        }
        const question = String(questionOverride ?? elements.input.value).trim();
        if (!question) return;
        if (!state.current) await createSession();

        appendMessage("user", question);
        elements.input.value = "";
        updateComposer();
        const assistant = appendMessage("assistant", "");
        const content = assistant.querySelector(".message-content");
        const actions = assistant.querySelector(".message-actions");
        actions.style.display = "none";
        content.innerHTML = `<p>正在准备制造知识查询…</p>`;
        let fullText = "";
        let buffer = "";
        state.abortController = new AbortController();
        setStreaming(true);

        try {
            const response = await fetch("/api/manufacturing-chat/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question,
                    session_id: state.current.id,
                }),
                signal: state.abortController.signal,
            });
            if (!response.ok || !response.body) throw new Error(`问答请求失败（HTTP ${response.status}）`);
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const events = buffer.split("\n\n");
                buffer = events.pop() || "";
                for (const event of events) {
                    const line = event.split("\n").find((item) => item.startsWith("data: "));
                    if (!line) continue;
                    let payload;
                    try { payload = JSON.parse(line.slice(6)); } catch (_) { continue; }
                    if (payload.type === "status") {
                        elements.statusText.textContent = payload.content;
                    } else if (payload.type === "chunk") {
                        fullText += payload.content || "";
                        content.innerHTML = renderMarkdown(fullText);
                        elements.stage.scrollTop = elements.stage.scrollHeight;
                    } else if (payload.type === "error") {
                        fullText = `### 问答未完成\n\n${payload.content}`;
                        content.innerHTML = `<div class="error-text">${renderMarkdown(fullText)}</div>`;
                    } else if (payload.type === "done") {
                        state.current.title = payload.session_title || state.current.title;
                        elements.title.textContent = state.current.title;
                    }
                }
            }
            actions.style.display = "flex";
            await refreshSessions();
        } catch (error) {
            if (error.name === "AbortError") {
                content.innerHTML = renderMarkdown(fullText || "已停止本次回答。已生成的内容不会作为完整答案保存。");
            } else {
                content.innerHTML = `<div class="error-text"><p>${escapeHtml(error.message)}</p></div>`;
            }
        } finally {
            state.abortController = null;
            setStreaming(false);
            elements.input.focus();
        }
    }

    async function loadConnectionStatus() {
        try {
            const status = await fetchJson("/api/manufacturing-chat/status");
            const ready = status.status === "ready";
            elements.connectionDot.className = `connection-dot ${ready ? "online" : "offline"}`;
            elements.connectionLabel.textContent = ready ? "制造知识服务在线" : "制造知识服务未就绪";
            elements.connectionDetail.textContent = status.detail || `Graph Studio ${status.graphstudio} · DeepSeek ${status.llm}`;
            elements.connectionDetail.title = status.graphmart_uri || status.detail || "";
        } catch (error) {
            elements.connectionDot.className = "connection-dot offline";
            elements.connectionLabel.textContent = "状态检查失败";
            elements.connectionDetail.textContent = error.message;
        }
    }

    function openMobileSidebar() { document.body.classList.add("sidebar-open"); }
    function closeMobileSidebar() { document.body.classList.remove("sidebar-open"); }

    elements.input.addEventListener("input", updateComposer);
    elements.input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendQuestion();
        }
    });
    elements.send.addEventListener("click", () => sendQuestion());
    $("#newChatButton").addEventListener("click", () => { if (!state.streaming) createSession(); });
    $("#clearConversation").addEventListener("click", () => state.current && deleteSession(state.current.id));
    elements.sessionSearch.addEventListener("input", () => { state.search = elements.sessionSearch.value; renderSessions(); });
    $("#quickPrompts").addEventListener("click", (event) => {
        const button = event.target.closest("[data-question]");
        if (button) sendQuestion(button.dataset.question);
    });
    elements.sessionList.addEventListener("click", (event) => {
        const deleteButton = event.target.closest("[data-delete-session]");
        if (deleteButton) {
            event.stopPropagation();
            deleteSession(deleteButton.dataset.deleteSession);
            return;
        }
        const item = event.target.closest("[data-session-id]");
        if (item) loadSession(item.dataset.sessionId);
    });
    elements.messages.addEventListener("click", async (event) => {
        const copyMessage = event.target.closest(".copy-message");
        if (copyMessage) {
            const text = copyMessage.closest(".message-body").querySelector(".message-content").innerText;
            await navigator.clipboard.writeText(text);
            showToast("回答已复制");
            return;
        }
        const copyCode = event.target.closest(".copy-code");
        if (copyCode) {
            await navigator.clipboard.writeText(copyCode.closest(".code-block").querySelector("pre").innerText);
            showToast("查询已复制");
        }
    });
    $("#openSidebar").addEventListener("click", openMobileSidebar);
    $("#closeSidebar").addEventListener("click", closeMobileSidebar);
    $("#sidebarScrim").addEventListener("click", closeMobileSidebar);

    async function initialize() {
        updateComposer();
        await Promise.allSettled([refreshSessions(), loadConnectionStatus()]);
        const lastSessionId = localStorage.getItem("manufacturing_qa_session_id");
        if (lastSessionId && state.sessions.some((item) => item.id === lastSessionId)) {
            await loadSession(lastSessionId);
        } else {
            setCurrentSession(null);
        }
        elements.input.focus();
    }

    initialize();
})();
