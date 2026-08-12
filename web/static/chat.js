/**
 * Camstar read-only SQL Assistant
 * ───────────────────────
 * Floating resizable chat panel with SSE streaming, multi-turn memory,
 * and graph node linking via [[ClassName]] markers.
 */
(() => {
    "use strict";

    const uiLanguage = () => window.CamstarI18n?.language || "zh-CN";
    const nodeLabel = (className) => {
        const node = (window.rawData?.nodes || []).find((item) => item.id === className);
        return window.CamstarI18n?.entity("node", className, {
            original: className,
            zh: node?.data?.chineseName || "",
        }) || className;
    };

    let sessionId = sessionStorage.getItem("chat_session_id") || null;
    let currentSession = null;
    let sessionReadyPromise = null;
    let isStreaming = false;
    let abortController = null;
    let chatHistoryArray = [];

    // ── DOM refs ──
    const chatBtn = document.getElementById("chatToggleBtn");
    const chatCloseBtn = document.getElementById("chatCloseBtn");
    const chatPanel = document.getElementById("chatPanel");
    const chatMessages = document.getElementById("chatMessages");
    const chatInput = document.getElementById("chatInput");
    const chatSend = document.getElementById("chatSend");
    const chatClear = document.getElementById("chatClearBtn");
    const chatNew = document.getElementById("chatNewBtn");
    const chatHistory = document.getElementById("chatHistoryBtn");
    const chatSessionMenu = document.getElementById("chatSessionMenu");
    const chatSessionList = document.getElementById("chatSessionList");
    const chatSessionCount = document.getElementById("chatSessionCount");
    const chatContextClasses = document.getElementById("chatContextClasses");
    const chatQuickActions = document.getElementById("chatQuickActions");
    const chatDialectSummary = document.getElementById("chatDialectSummary");

    const SQL_DIALECTS = {
        oracle: {
            label: "Oracle",
            params: ":StartTime 和 :EndTime",
        },
        sqlserver: {
            label: "SQL Server",
            params: "@StartTime 和 @EndTime",
        },
    };

    function normalizeSqlDialect(value) {
        return Object.hasOwn(SQL_DIALECTS, value) ? value : "oracle";
    }

    let selectedSqlDialect = normalizeSqlDialect(
        typeof window._getSqlDialect === "function" ? window._getSqlDialect() : "oracle",
    );

    function getWelcomeHtml() {
        const label = SQL_DIALECTS[selectedSqlDialect].label;
        if (uiLanguage() === "en-US") {
            return `<div class="chat-welcome">
                <img src="/static/siemens_logo.svg" alt="Opcenter" class="chat-welcome-icon" style="width:48px;height:48px;border-radius:8px;margin:0 auto 12px;display:block;" />
                <p>Hello! Describe the business data you need to query.</p>
                <p class="chat-welcome-sub">Add known objects from the graph or type @table; I will generate read-only ${label} SQL from verified physical fields and relationships.</p>
            </div>`;
        }
        return `<div class="chat-welcome">
            <img src="/static/siemens_logo.svg" alt="Opcenter" class="chat-welcome-icon" style="width:48px;height:48px;border-radius:8px;margin:0 auto 12px;display:block;" />
            <p>你好！请描述需要查询的业务数据。</p>
            <p class="chat-welcome-sub">可从左侧加入已知对象，或输入 @表名；我会依据真实物理字段和关系生成只读 ${label} SQL</p>
        </div>`;
    }

    function applySqlDialect(value) {
        selectedSqlDialect = normalizeSqlDialect(value);
        chatDialectSummary.textContent = `${SQL_DIALECTS[selectedSqlDialect].label} SQL`;
        if (!chatHistoryArray.length) {
            chatMessages.innerHTML = getWelcomeHtml();
        }
    }

    applySqlDialect(selectedSqlDialect);
    window.addEventListener("camstar:sql-dialect-change", (event) => {
        applySqlDialect(event.detail?.dialect);
    });
    window.addEventListener("camstar:i18n-change", () => {
        if (!chatHistoryArray.length) chatMessages.innerHTML = getWelcomeHtml();
        updateContextBar(currentSession?.context);
    });

    function stopStreaming() {
        // Abort any in-flight stream
        if (abortController) {
            abortController.abort();
            abortController = null;
        }
        isStreaming = false;
        chatSend.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>`;
        chatSend.classList.remove("chat-stop-btn");
    }

    function setCurrentSession(session) {
        currentSession = session;
        sessionId = session.id;
        sessionStorage.setItem("chat_session_id", sessionId);
        chatHistoryArray = (session.messages || []).map((message) => ({
            role: message.role,
            content: message.content || "",
        }));
        updateContextBar(session.context);
        chatMessages.innerHTML = chatHistoryArray.length ? "" : getWelcomeHtml();
        for (const message of chatHistoryArray) {
            const bubble = appendMessage(message.role, message.content);
            if (message.role === "assistant") {
                addSqlCopyButtons(bubble.querySelector(".chat-msg-content"));
            }
        }
        chatInput.value = "";
        chatInput.style.height = "auto";
    }

    function getKnownClasses(context = currentSession?.context) {
        return [...(context?.known_classes || [])];
    }

    function updateContextBar(context) {
        const classes = getKnownClasses(context);
        chatContextClasses.innerHTML = classes.length
            ? classes.map((className) => `
                <span class="chat-context-chip" data-class="${escapeHtml(className)}">
                    <span class="chat-context-chip-name" title="${uiLanguage() === "en-US" ? "Locate in graph" : "在图中定位"} ${escapeHtml(className)}">${escapeHtml(nodeLabel(className))}</span>
                    <button type="button" class="chat-context-chip-remove"
                        data-remove-class="${escapeHtml(className)}"
                        aria-label="删除 ${escapeHtml(className)}"
                        title="从上下文删除">×</button>
                </span>
            `).join("")
            : `<span class="chat-context-empty">${uiLanguage() === "en-US" ? "No known objects added" : "尚未添加已知对象"}</span>`;
        chatContextClasses.title = classes.join(", ");
        window.dispatchEvent(new CustomEvent("chat-context-change", {
            detail: { classes },
        }));
    }

    async function saveKnownClasses(classes) {
        const session = await ensureSession();
        const normalized = [...new Set(classes)].slice(0, 8);
        const response = await fetch(
            `/api/chat/sessions/${encodeURIComponent(session.id)}/context`,
            {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ known_classes: normalized }),
            },
        );
        if (!response.ok) {
            let detail = `HTTP ${response.status}`;
            try {
                const payload = await response.json();
                detail = payload.detail || payload.error || detail;
            } catch (_) {}
            throw new Error(detail);
        }
        const updatedSession = await response.json();
        currentSession = updatedSession;
        sessionId = updatedSession.id;
        sessionStorage.setItem("chat_session_id", sessionId);
        updateContextBar(updatedSession.context);
        await refreshSessionList();
        return getKnownClasses(updatedSession.context);
    }

    window._hasChatContextClass = (className) =>
        getKnownClasses().includes(className);

    window._addChatContextClass = async (className) => {
        const session = await ensureSession();
        const current = getKnownClasses(session.context);
        if (current.includes(className)) return current;
        if (current.length >= 8) {
            throw new Error("当前会话最多添加 8 个已知对象");
        }
        const classes = await saveKnownClasses([...current, className]);
        if (chatPanel.classList.contains("chat-hidden")) {
            chatPanel.classList.remove("chat-hidden");
            chatBtn.classList.add("active");
        }
        return classes;
    };

    window._continueSqlDraft = async (classNames, sql) => {
        await ensureSession();
        const queryClasses = [...new Set(
            Array.isArray(classNames) ? classNames : [],
        )];
        if (queryClasses.length > 8) {
            throw new Error("当前会话最多添加 8 个已知对象");
        }
        // A query-builder handoff is an explicit context boundary. Replace
        // stale chat objects so they cannot silently influence this SQL draft.
        await saveKnownClasses(queryClasses);
        if (chatPanel.classList.contains("chat-hidden")) {
            chatPanel.classList.remove("chat-hidden");
            chatBtn.classList.add("active");
        }
        chatInput.value = (
            "请基于以下经过物理外键验证的 SQL 骨架，继续补充查询条件和返回字段：\n\n"
            + sql
        );
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + "px";
        chatInput.focus();
    };

    async function createNewSession() {
        stopStreaming();
        const product_line = (typeof window._getCurrentProductLine === "function")
            ? window._getCurrentProductLine()
            : "general";
        const response = await fetch("/api/chat/sessions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title: uiLanguage() === "en-US" ? "New SQL Session" : "新建 SQL 会话",
                assistant_mode: "sql",
                product_line,
            }),
        });
        if (!response.ok) throw new Error(`创建会话失败: HTTP ${response.status}`);
        const session = await response.json();
        setCurrentSession(session);
        chatSessionMenu.classList.add("chat-session-menu-hidden");
        await refreshSessionList();
        return session;
    }

    async function loadSession(targetSessionId) {
        stopStreaming();
        const response = await fetch(
            `/api/chat/sessions/${encodeURIComponent(targetSessionId)}`,
            { cache: "no-store" },
        );
        if (!response.ok) throw new Error(`加载会话失败: HTTP ${response.status}`);
        const session = await response.json();
        setCurrentSession(session);
        chatSessionMenu.classList.add("chat-session-menu-hidden");
        return session;
    }

    async function ensureSession() {
        if (currentSession) return currentSession;
        if (sessionReadyPromise) return sessionReadyPromise;
        sessionReadyPromise = (async () => {
            if (sessionId) {
                try {
                    return await loadSession(sessionId);
                } catch (_) {
                    sessionStorage.removeItem("chat_session_id");
                    sessionId = null;
                }
            }
            return createNewSession();
        })().finally(() => {
            sessionReadyPromise = null;
        });
        return sessionReadyPromise;
    }

    function formatSessionTime(value) {
        if (!value) return "";
        const date = new Date(value);
        return Number.isNaN(date.getTime())
            ? ""
            : date.toLocaleString("zh-CN", { hour12: false });
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    async function refreshSessionList() {
        const response = await fetch("/api/chat/sessions?limit=100", {
            cache: "no-store",
        });
        if (!response.ok) return;
        const payload = await response.json();
        const items = payload.items || [];
        chatSessionCount.textContent = items.length;
        chatSessionList.innerHTML = items.length
            ? items.map((item) => `
                <div class="chat-session-item ${item.id === sessionId ? "active" : ""}" data-session-id="${item.id}">
                    <div class="chat-session-item-title">${escapeHtml(item.title || "未命名会话")}</div>
                    <div class="chat-session-item-meta">${escapeHtml(formatSessionTime(item.updated_at))} · ${item.message_count || 0} 条消息${item.known_classes?.length ? ` · 已知对象 ${escapeHtml(item.known_classes.join(", "))}` : ""}</div>
                    <div class="chat-session-item-preview">${escapeHtml(item.preview || "暂无消息")}</div>
                </div>
            `).join("")
            : `<div class="chat-session-item-preview" style="padding:16px;text-align:center">暂无历史会话</div>`;
    }

    // ── Toggle panel (topbar button) ──
    chatBtn.addEventListener("click", async () => {
        const wasHidden = chatPanel.classList.contains("chat-hidden");
        chatPanel.classList.toggle("chat-hidden");
        chatBtn.classList.toggle("active", wasHidden);
        if (wasHidden) {
            await ensureSession();
            chatInput.focus();
        }
    });

    function closeChatPanel() {
        chatPanel.classList.add("chat-hidden");
        chatBtn.classList.remove("active");
        chatSessionMenu.classList.add("chat-session-menu-hidden");
        closeMention();
    }

    window._closeChatPanel = closeChatPanel;

    // ── Close panel (header X button) ──
    chatCloseBtn.addEventListener("click", closeChatPanel);

    // ── Send message ──
    chatSend.addEventListener("click", () => {
        if (isStreaming) {
            if (abortController) abortController.abort();
        } else {
            sendMessage();
        }
    });
    // ── @ Mention Logic & Auto-resize ──
    const mentionDropdown = document.getElementById("mentionDropdown");
    let mentionActive = false;
    let mentionQuery = "";
    let mentionMatchStart = -1;
    let mentionMatchEnd = -1;
    let mentionIndex = -1;
    let mentionItems = [];

    chatInput.addEventListener("input", function(e) {
        // Auto resize
        this.style.height = "auto";
        this.style.height = (this.scrollHeight) + "px";
        if (this.value === "") {
            this.style.height = "auto";
        }

        // @ mention trigger check
        const cursorPosition = this.selectionStart;
        const textBeforeCursor = this.value.substring(0, cursorPosition);
        
        // Match "@" followed by at least one character at the end of the string before cursor
        const match = textBeforeCursor.match(/@([a-zA-Z0-9_\u4e00-\u9fa5]+)$/);
        
        if (match) {
            mentionActive = true;
            mentionQuery = match[1].toLowerCase();
            mentionMatchStart = match.index;
            mentionMatchEnd = cursorPosition;
            updateMentionDropdown();
        } else {
            closeMention();
        }
    });

    function closeMention() {
        mentionActive = false;
        mentionDropdown.style.display = "none";
        mentionIndex = -1;
    }

    function updateMentionDropdown() {
        if (!window.rawData || !window.rawData.nodes) return;
        
        mentionItems = window.rawData.nodes.filter(n => {
            const id = n.id.toLowerCase();
            const cn = (n.data?.chineseName || "").toLowerCase();
            return id.startsWith(mentionQuery) || cn.startsWith(mentionQuery);
        }).slice(0, 10);

        if (mentionItems.length === 0) {
            closeMention();
            return;
        }

        mentionDropdown.innerHTML = mentionItems.map((n, i) => `
            <div class="mention-item ${i === 0 ? 'active' : ''}" data-index="${i}">
                <span class="mention-item-name">${n.id}</span>
                <span class="mention-item-desc">${n.data?.chineseName || ""}</span>
            </div>
        `).join("");

        mentionIndex = 0;
        mentionDropdown.style.display = "block";

        mentionDropdown.querySelectorAll(".mention-item").forEach(el => {
            el.addEventListener("mousedown", (e) => {
                e.preventDefault(); // keep focus
                selectMention(parseInt(el.dataset.index));
            });
        });
    }

    function selectMention(index) {
        if (index < 0 || index >= mentionItems.length) return;
        const selected = mentionItems[index];
        const val = chatInput.value;
        const textBefore = val.substring(0, mentionMatchStart);
        const textAfter = val.substring(mentionMatchEnd);
        
        // Insert node ID with brackets for the chat agent to parse
        const insertText = `[[${selected.id}]] `;
        chatInput.value = textBefore + insertText + textAfter;
        chatInput.selectionStart = chatInput.selectionEnd = textBefore.length + insertText.length;
        closeMention();
        chatInput.focus();
    }

    function renderMentionSelection() {
        const items = mentionDropdown.querySelectorAll(".mention-item");
        items.forEach((el, i) => {
            if (i === mentionIndex) el.classList.add("active");
            else el.classList.remove("active");
        });
        if (items[mentionIndex]) {
            items[mentionIndex].scrollIntoView({ block: "nearest" });
        }
    }

    chatInput.addEventListener("keydown", (e) => {
        if (mentionActive) {
            if (e.key === "ArrowDown") {
                e.preventDefault();
                mentionIndex = (mentionIndex + 1) % mentionItems.length;
                renderMentionSelection();
                return;
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                mentionIndex = (mentionIndex - 1 + mentionItems.length) % mentionItems.length;
                renderMentionSelection();
                return;
            } else if (e.key === "Enter" || e.key === "Tab") {
                e.preventDefault();
                selectMention(mentionIndex);
                return;
            } else if (e.key === "Escape") {
                e.preventDefault();
                closeMention();
                return;
            }
        }

        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // ── Persistent session controls ──
    chatNew.addEventListener("click", async () => {
        try {
            await createNewSession();
            chatInput.focus();
        } catch (error) {
            console.error(error);
        }
    });

    chatQuickActions.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-prompt]");
        if (!button || isStreaming) return;
        const selected = (typeof window._getSelectedNodeId === "function")
            ? window._getSelectedNodeId()
            : null;
        const knownClasses = getKnownClasses();
        const subject = selected
            ? `[[${selected}]]`
            : knownClasses.length
                ? knownClasses.map((name) => `[[${name}]]`).join("、")
                : "当前选中的表";
        const dialect = SQL_DIALECTS[selectedSqlDialect];
        const prompts = {
            fields: `请列出 ${subject} 最常用于写SQL的物理字段、主键和外键，并说明适合的查询场景。`,
            time: `请基于 ${subject} 生成一个${dialect.label} SQL时间范围查询模板，使用 ${dialect.params} 参数。`,
            move: `请生成按Container名称和时间范围查询完整过站Move轨迹的${dialect.label} SQL。`,
            throughput: `请生成按工序和时间范围统计产出数量的${dialect.label} SQL，并说明数量和去重口径。`,
        };
        chatInput.value = prompts[button.dataset.prompt] || "";
        chatInput.focus();
    });

    chatHistory.addEventListener("click", async () => {
        const opening = chatSessionMenu.classList.contains("chat-session-menu-hidden");
        chatSessionMenu.classList.toggle("chat-session-menu-hidden");
        if (opening) await refreshSessionList();
    });

    chatContextClasses.addEventListener("click", async (event) => {
        const removeButton = event.target.closest("button[data-remove-class]");
        if (removeButton) {
            if (isStreaming) return;
            const className = removeButton.dataset.removeClass;
            removeButton.disabled = true;
            try {
                await saveKnownClasses(
                    getKnownClasses().filter((name) => name !== className),
                );
            } catch (error) {
                removeButton.disabled = false;
                console.error("Remove SQL context failed:", error);
            }
            return;
        }

        const chip = event.target.closest(".chat-context-chip[data-class]");
        if (chip && typeof window._locateNodeWithoutEdges === "function") {
            window._locateNodeWithoutEdges(chip.dataset.class, true);
        }
    });

    chatSessionList.addEventListener("click", async (event) => {
        const item = event.target.closest(".chat-session-item[data-session-id]");
        if (!item) return;
        try {
            await loadSession(item.dataset.sessionId);
            chatInput.focus();
        } catch (error) {
            console.error(error);
        }
    });

    chatClear.addEventListener("click", async () => {
        stopStreaming();
        if (sessionId) {
            try {
                await fetch(`/api/chat/sessions/${encodeURIComponent(sessionId)}`, {
                    method: "DELETE",
                });
            } catch (_) {}
        }
        sessionId = null;
        currentSession = null;
        sessionStorage.removeItem("chat_session_id");
        await createNewSession();
        chatInput.focus();
    });

    // ══════════════════════════════════════════════════════
    //  Resize Logic
    // ══════════════════════════════════════════════════════
    const resizeHandles = chatPanel.querySelectorAll(".chat-resize-handle");
    resizeHandles.forEach((handle) => {
        handle.addEventListener("mousedown", initResize);
    });

    function initResize(e) {
        e.preventDefault();
        e.stopPropagation();
        const dir = e.target.dataset.dir;
        const startX = e.clientX;
        const startY = e.clientY;
        const startW = chatPanel.offsetWidth;
        const startH = chatPanel.offsetHeight;
        const startRight = parseInt(chatPanel.style.right || "12");

        // Disable transitions during drag
        chatPanel.style.transition = "none";

        function onMouseMove(ev) {
            const dx = ev.clientX - startX;
            const dy = ev.clientY - startY;

            if (dir === "left" || dir === "corner") {
                // Dragging left edge → increase width, shift right stays same
                const newW = Math.max(360, Math.min(800, startW - dx));
                chatPanel.style.width = newW + "px";
            }
            if (dir === "bottom" || dir === "corner") {
                const newH = Math.max(300, startH + dy);
                chatPanel.style.height = newH + "px";
            }
        }

        function onMouseUp() {
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
            chatPanel.style.transition = "";
        }

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    }

    // ══════════════════════════════════════════════════════
    //  Streaming Chat
    // ══════════════════════════════════════════════════════
    async function sendMessage() {
        await ensureSession();
        const question = chatInput.value.trim();
        if (!question || isStreaming) return;

        // Add user message bubble
        appendMessage("user", question);
        chatHistoryArray.push({ role: "user", content: question });
        chatInput.value = "";
        chatInput.style.height = "auto"; // Reset height
        isStreaming = true;
        
        // Change button to STOP
        chatSend.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="6" width="12" height="12" fill="currentColor"/></svg>`;
        chatSend.classList.add("chat-stop-btn");

        // Create assistant bubble
        const assistantBubble = appendMessage("assistant", "");
        const contentEl = assistantBubble.querySelector(".chat-msg-content");
        contentEl.innerHTML = `<span class="chat-typing">思考中...</span>`;

        let highlightData = null; // Store highlight data to append link after final render
        abortController = new AbortController();

        try {
            const product_line = (typeof window._getCurrentProductLine === "function") ? window._getCurrentProductLine() : "general";
            const selectedNode = (typeof window._getSelectedNodeId === "function") ? window._getSelectedNodeId() : null;
            const knownClasses = getKnownClasses();
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question,
                    session_id: sessionId,
                    product_line,
                    assistant_mode: "sql",
                    sql_dialect: selectedSqlDialect,
                    selected_classes: [
                        ...knownClasses,
                        ...(selectedNode ? [selectedNode] : []),
                    ]
                }),
                signal: abortController.signal
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = "";
            let buffer = "";
            let lastRenderTime = 0;
            const RENDER_THROTTLE_MS = 100; // Render at most once every 100ms to keep CPU load low

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    try {
                        const payload = JSON.parse(line.slice(6));
                        if (payload.type === "chunk") {
                            fullText += payload.content;
                            const now = Date.now();
                            if (now - lastRenderTime > RENDER_THROTTLE_MS) {
                                contentEl.innerHTML = renderMarkdown(fullText);
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                                lastRenderTime = now;
                            }
                        } else if (payload.type === "status") {
                            contentEl.innerHTML = `<div class="chat-status-indicator" style="display:flex;align-items:center;gap:8px;color:var(--si-green);font-style:italic;margin-bottom:8px;"><span class="wiki-spinner" style="display:inline-block;width:12px;height:12px;border:2px solid rgba(0, 153, 153, 0.2);border-top-color:var(--si-green);border-radius:50%;animation:spin 0.8s linear infinite;"></span>${payload.content}</div>`;
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        } else if (payload.type === "done") {
                            sessionId = payload.session_id || sessionId;
                            sessionStorage.setItem("chat_session_id", sessionId);
                            if (payload.session_title && currentSession) {
                                currentSession.title = payload.session_title;
                            }
                            if (payload.session_context) {
                                if (currentSession) currentSession.context = payload.session_context;
                                updateContextBar(payload.session_context);
                            }
                            if (payload.highlight) {
                                highlightData = payload.highlight;
                                if (typeof window._highlightGraph === "function") {
                                    window._highlightGraph(payload.highlight);
                                }
                            }
                        } else if (payload.type === "error") {
                            contentEl.innerHTML = `<span class="icon-label" style="color:#FF6666">${AppIcons.svg("xCircle", { size: 15 })}<span>${escapeHtml(payload.content)}</span></span>`;
                        }
                    } catch (_) {}
                }
            }

            // Final render with links
            contentEl.innerHTML = renderMarkdown(fullText);
            addSqlCopyButtons(contentEl);
            
            // Append in-bubble highlight link if highlightData exists
            if (highlightData) {
                appendHighlightLink(contentEl, highlightData);
            }
            
            // Save to history
            chatHistoryArray.push({ role: "assistant", content: fullText, highlightData });
            await refreshSessionList();
            
            chatMessages.scrollTop = chatMessages.scrollHeight;

        } catch (err) {
            if (err.name === 'AbortError') {
                contentEl.innerHTML += `<br/><span style="color:#FF6666;font-size:12px;margin-top:4px;display:block;"><i>[已终止当前生成]</i></span>`;
            } else {
                contentEl.innerHTML = `<span style="color:#FF6666">连接失败: ${err.message}</span>`;
            }
        } finally {
            isStreaming = false;
            abortController = null;
            chatSend.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>`;
            chatSend.classList.remove("chat-stop-btn");
        }
    }

    function appendMessage(role, content) {
        const wrapper = document.createElement("div");
        wrapper.className = `chat-msg chat-msg-${role}`;
        const avatar = role === "user"
            ? AppIcons.svg("user", { size: 20 })
            : '<img src="/static/siemens_logo.svg" alt="Opcenter" style="width:24px;height:24px;border-radius:4px;" />';
        wrapper.innerHTML = `
            <div class="chat-msg-avatar" style="background:transparent;padding:0;">${avatar}</div>
            <div class="chat-msg-bubble">
                <div class="chat-msg-content">${content ? renderMarkdown(content) : ""}</div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return wrapper;
    }

    function renderMarkdown(text) {
        if (!text) return "";
        let html = escapeHtml(text)
            .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="chat-code"><code>$2</code></pre>')
            .replace(/`([^`]+)`/g, '<code class="chat-inline-code">$1</code>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/^### 查询理解\r?\n\r?\n((?:^- .+(?:\r?\n|$))+)/gm, '<div class="chat-query-plan"><div class="chat-query-plan-title">查询理解</div>\n$1</div>')
            .replace(/^### 需要你确认$/gm, '<div class="chat-clarification-title">需要你确认</div>')
            .replace(/^### (.+)$/gm, '<div class="chat-h3">$1</div>')
            .replace(/^## (.+)$/gm, '<div class="chat-h2">$1</div>')
            .replace(/^- (.+)$/gm, '<div class="chat-li">• $1</div>')
            .replace(/^(\d+)\. (.+)$/gm, '<div class="chat-li">$1. $2</div>')
            .replace(/\[\[(\w+)\]\]/g, '<span class="chat-class-link" data-class="$1">$1</span>')
            .replace(/\n/g, '<br/>');
        return html;
    }

    function addSqlCopyButtons(container) {
        container.querySelectorAll("pre.chat-code").forEach((pre) => {
            if (pre.querySelector(".sql-copy-btn")) return;
            pre.style.position = "relative";
            const button = document.createElement("button");
            button.type = "button";
            button.className = "sql-copy-btn";
            button.textContent = "复制 SQL";
            button.style.cssText = "position:absolute;right:8px;top:8px;padding:4px 8px;border:1px solid rgba(0,255,185,.35);border-radius:4px;background:#062734;color:#00ffb9;font-size:11px;cursor:pointer";
            button.addEventListener("click", async () => {
                const code = pre.querySelector("code")?.textContent || "";
                await navigator.clipboard.writeText(code);
                button.textContent = "已复制";
                setTimeout(() => { button.textContent = "复制 SQL"; }, 1200);
            });
            pre.appendChild(button);
        });
    }

    // ── Click on [[ClassName]] links in chat ──
    chatMessages.addEventListener("click", (e) => {
        if (e.target.classList.contains("chat-class-link")) {
            const className = e.target.dataset.class;
            if (!className) return;
            if (typeof window._locateNodeWithoutEdges === "function") {
                window._locateNodeWithoutEdges(className, true);
            }
        }
    });

    // ── Append highlight link button helper ──
    function appendHighlightLink(contentEl, highlightData) {
        const highlightLink = document.createElement("div");
        highlightLink.className = "chat-bubble-highlight-link";
        highlightLink.style.cssText = "display:inline-flex;align-items:center;gap:4px;color:var(--si-green);font-size:11px;font-weight:600;margin-top:8px;cursor:pointer;user-select:none;opacity:0.8;transition:opacity 0.2s;";
        highlightLink.innerHTML = `
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;">
                <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
                <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
            </svg>
            高亮此关系图谱
        `;
        highlightLink.addEventListener("mouseenter", () => highlightLink.style.opacity = "1");
        highlightLink.addEventListener("mouseleave", () => highlightLink.style.opacity = "0.8");
        highlightLink.addEventListener("click", (e) => {
            e.stopPropagation();
            if (typeof window._highlightGraph === "function") {
                window._highlightGraph(highlightData);
            }
        });
        contentEl.appendChild(highlightLink);
    }

    // No load restoration. Click chat starts a fresh session.

    // ── Expose programmatic question sender for edge popup ──
    window._askQuestion = function(questionText) {
        // Open chat panel if hidden
        if (chatPanel.classList.contains("chat-hidden")) {
            chatPanel.classList.remove("chat-hidden");
            chatBtn.classList.add("active");
        }
        chatInput.value = questionText;
        setTimeout(() => sendMessage(), 100);
    };
})();
