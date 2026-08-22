import {
  ApiOutlined,
  CheckCircleFilled,
  CopyOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  App,
  Avatar,
  Button,
  Empty,
  Input,
  List,
  Select,
  Space,
  Spin,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { manufacturingApi, streamManufacturingAnswer } from "../api";
import { queryBusinessTitle } from "../format";
import type { ChatMessage, ChatSession, SavedQuery } from "../types";

const QUICK_QUESTIONS = [
  "当前发布了哪些制造订单？",
  "每个制造订单分别关联了什么产品？",
  "按产品统计关联的制造订单数量。",
  "当前知识图谱中有哪些对象类型和关系？",
];

function ComposerSendIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 19V5M6.5 10.5 12 5l5.5 5.5" />
    </svg>
  );
}

function ComposerStopIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="8" y="8" width="8" height="8" rx="1" />
    </svg>
  );
}

function MessageContent({ message }: { message: ChatMessage }) {
  const isAssistant = message.role === "assistant";
  return (
    <div className={`chat-message ${message.role}`}>
      {isAssistant && (
        <div className="message-author">
          <Avatar className="message-avatar" size={28}>MG</Avatar>
          <span>制造知识助手</span>
        </div>
      )}
      <div className="message-column">
        <div className="message-bubble markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content || "正在准备制造知识查询…"}</ReactMarkdown>
        </div>
        {isAssistant && message.content && (
          <Space size={6} wrap>
            {message.runtime && <Tag color="cyan">本体 R{message.runtime.ontologyReleaseNo} · 数据 R{message.runtime.curatedReleaseNo}</Tag>}
            <Tooltip title="复制回答"><Button className="copy-answer" type="text" size="small" icon={<CopyOutlined />} aria-label="复制回答" onClick={() => navigator.clipboard.writeText(message.content)} /></Tooltip>
          </Space>
        )}
      </div>
    </div>
  );
}

export function AssistantPage() {
  const { message, modal } = App.useApp();
  const queryClient = useQueryClient();
  const [current, setCurrent] = useState<ChatSession | null>(null);
  const [sessionSearch, setSessionSearch] = useState("");
  const [question, setQuestion] = useState("");
  const [queryChoice, setQueryChoice] = useState("auto");
  const [streaming, setStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState("");
  const [refreshingKnowledge, setRefreshingKnowledge] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  const sessions = useQuery({ queryKey: ["chat-sessions"], queryFn: manufacturingApi.sessions });
  const savedQueries = useQuery({ queryKey: ["saved-queries"], queryFn: () => manufacturingApi.queries() });
  const serviceStatus = useQuery({ queryKey: ["manufacturing-status"], queryFn: () => manufacturingApi.status(), refetchInterval: 30_000 });
  const runtime = serviceStatus.data?.runtime;

  const refreshKnowledge = async () => {
    setRefreshingKnowledge(true);
    try {
      const [queries, status] = await Promise.all([
        manufacturingApi.queries(true),
        manufacturingApi.status(true),
      ]);
      queryClient.setQueryData(["saved-queries"], queries);
      queryClient.setQueryData(["manufacturing-status"], status);
      message.success(`已同步本体 R${status.runtime?.ontologyReleaseNo || "—"} / 数据 R${status.runtime?.curatedReleaseNo || "—"}`);
    } catch (error) {
      message.error((error as Error).message);
    } finally {
      setRefreshingKnowledge(false);
    }
  };

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [current?.messages, streaming]);

  const filteredSessions = useMemo(() => {
    const term = sessionSearch.trim().toLowerCase();
    return (sessions.data?.items || []).filter((item) =>
      !term || `${item.title} ${item.preview || ""}`.toLowerCase().includes(term),
    );
  }, [sessionSearch, sessions.data?.items]);

  const queryOptions = [
    { value: "auto", label: "自动匹配已保存 Query" },
    ...(savedQueries.data?.items || []).filter((item) => item.compatible !== false).map((item: SavedQuery) => ({ value: item.uri, label: queryBusinessTitle(item) })),
    { value: "dynamic", label: "动态只读查询" },
  ];

  const loadSession = async (id: string) => {
    if (streaming) return;
    try {
      const session = await manufacturingApi.session(id);
      setCurrent(session);
      localStorage.setItem("manufacturing_react_session_id", id);
    } catch (error) {
      message.error((error as Error).message);
    }
  };

  useEffect(() => {
    const lastId = localStorage.getItem("manufacturing_react_session_id");
    if (lastId && !current && sessions.data?.items.some((item) => item.id === lastId)) {
      void loadSession(lastId);
    }
  }, [sessions.data]);

  const createSession = async () => {
    const session = await manufacturingApi.createSession();
    setCurrent(session);
    localStorage.setItem("manufacturing_react_session_id", session.id);
    await queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    return session;
  };

  const removeSession = (id: string) => {
    modal.confirm({
      title: "删除该问答会话？",
      content: "会话历史将从本地制造问答记录中移除。",
      okText: "删除",
      okButtonProps: { danger: true },
      cancelText: "取消",
      onOk: async () => {
        await manufacturingApi.deleteSession(id);
        if (current?.id === id) {
          setCurrent(null);
          localStorage.removeItem("manufacturing_react_session_id");
        }
        await queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      },
    });
  };

  const sendQuestion = async (quickQuestion?: string) => {
    if (streaming) {
      abortRef.current?.abort();
      return;
    }
    const text = (quickQuestion ?? question).trim();
    if (!text) return;
    let activeSession = current;
    if (!activeSession) activeSession = await createSession();

    const workingMessages: ChatMessage[] = [
      ...(activeSession.messages || []),
      { role: "user", content: text },
      { role: "assistant", content: "", runtime },
    ];
    setCurrent({ ...activeSession, messages: workingMessages });
    setQuestion("");
    setStreaming(true);
    setStreamStatus("正在准备制造知识查询…");
    const controller = new AbortController();
    abortRef.current = controller;
    let answer = "";

    try {
      await streamManufacturingAnswer(
        {
          question: text,
          sessionId: activeSession.id,
          queryMode: queryChoice === "dynamic" ? "dynamic" : "auto",
          queryUri: queryChoice !== "auto" && queryChoice !== "dynamic" ? queryChoice : undefined,
        },
        (event) => {
          if (event.type === "status") setStreamStatus(event.content || "正在查询");
          if (event.type === "chunk") {
            answer += event.content || "";
            setCurrent((previous) => {
              if (!previous) return previous;
              const messages = [...previous.messages];
              messages[messages.length - 1] = { ...messages[messages.length - 1], role: "assistant", content: answer };
              return { ...previous, messages, title: event.session_title || previous.title };
            });
          }
          if (event.type === "error") {
            answer = `### 问答未完成\n\n${event.content || "制造知识服务暂时不可用"}`;
            setCurrent((previous) => {
              if (!previous) return previous;
              const messages = [...previous.messages];
              messages[messages.length - 1] = { ...messages[messages.length - 1], role: "assistant", content: answer };
              return { ...previous, messages };
            });
          }
          if (event.type === "done" && event.session_title) {
            setCurrent((previous) => {
              if (!previous) return previous;
              const messages = [...previous.messages];
              messages[messages.length - 1] = { ...messages[messages.length - 1], runtime: event.runtime || messages[messages.length - 1].runtime };
              return { ...previous, messages, title: event.session_title!, runtime: event.runtime || previous.runtime };
            });
          }
        },
        controller.signal,
      );
      await queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
    } catch (error) {
      if ((error as Error).name !== "AbortError") message.error((error as Error).message);
    } finally {
      abortRef.current = null;
      setStreaming(false);
      setStreamStatus("");
    }
  };

  return (
    <div className="assistant-workspace">
      <aside className="conversation-panel">
        <Button type="primary" icon={<PlusOutlined />} block onClick={() => void createSession()}>新建制造问答</Button>
        <Input.Search value={sessionSearch} onChange={(event) => setSessionSearch(event.target.value)} placeholder="搜索历史会话" allowClear />
        <div className="conversation-heading"><span>历史记录</span><Tag>{filteredSessions.length}</Tag></div>
        <List
          className="conversation-list"
          loading={sessions.isLoading}
          dataSource={filteredSessions}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无问答记录" /> }}
          renderItem={(item) => (
            <List.Item className={current?.id === item.id ? "active" : ""} onClick={() => void loadSession(item.id)}>
              <List.Item.Meta title={item.title || "制造知识问答"} description={`${Math.ceil((item.message_count || 0) / 2)} 轮问答`} />
              <Tooltip title="删除会话"><Button type="text" danger icon={<DeleteOutlined />} onClick={(event) => { event.stopPropagation(); removeSession(item.id); }} /></Tooltip>
            </List.Item>
          )}
        />
        <div className="assistant-service-card">
          <CheckCircleFilled className={serviceStatus.data?.status === "ready" ? "online" : "checking"} />
          <span><strong>{serviceStatus.data?.status === "ready" ? "制造知识服务在线" : "正在检查知识服务"}</strong><small>{runtime ? `本体 R${runtime.ontologyReleaseNo} · 数据 R${runtime.curatedReleaseNo}` : `${savedQueries.data?.count ?? 0} 条受控 Query`}</small></span>
        </div>
      </aside>

      <section className="chat-panel">
        <div className="chat-toolbar">
          <div><Typography.Text strong>{current?.title || "制造知识问答"}</Typography.Text><Typography.Text type="secondary">答案严格基于当前活动部署、本体契约与 Graphmart 证据</Typography.Text></div>
          <Space>
            {runtime && <Tag color="cyan">本体 R{runtime.ontologyReleaseNo} · {runtime.ontologyClassCount} 类 / {runtime.ontologyRelationshipCount} 关系</Tag>}
            {runtime && <Tag color="blue">数据 R{runtime.curatedReleaseNo}</Tag>}
            <ApiOutlined />
            <Select value={queryChoice} options={queryOptions} onChange={setQueryChoice} disabled={streaming} popupMatchSelectWidth={300} />
            <Tooltip title="强制同步最新部署、Schema 与 Graph Studio Queries"><Button icon={<ReloadOutlined />} loading={refreshingKnowledge} onClick={() => void refreshKnowledge()} /></Tooltip>
          </Space>
        </div>

        <div className="messages-viewport">
          {!current?.messages?.length ? (
            <div className="assistant-welcome">
              <Avatar size={64}>MG</Avatar>
              <Tag color="cyan">GRAPH STUDIO GROUNDED ANSWERS</Tag>
              <Typography.Title level={2}>从制造知识图谱中获得可追溯答案</Typography.Title>
              <Typography.Paragraph>优先匹配经过治理的 Graph Studio Query；没有合适能力时，再生成安全的动态只读查询。</Typography.Paragraph>
              <div className="quick-question-grid">
                {QUICK_QUESTIONS.map((item) => <Button key={item} onClick={() => void sendQuestion(item)}>{item}</Button>)}
              </div>
            </div>
          ) : current.messages.map((item, index) => <MessageContent key={`${item.role}-${index}`} message={item} />)}
          {streaming && <div className="stream-indicator"><Spin size="small" /><span>{streamStatus}</span></div>}
          <div ref={endRef} />
        </div>

        <div className="chat-composer-wrap">
          <div className="chat-composer">
            <Input.TextArea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onPressEnter={(event) => {
                if (!event.shiftKey) {
                  event.preventDefault();
                  void sendQuestion();
                }
              }}
              autoSize={{ minRows: 1, maxRows: 6 }}
              placeholder="询问制造订单、产品、质量及其关系…"
              disabled={streaming}
            />
            <Button
              className={`composer-submit ${streaming ? "is-streaming" : ""}`}
              type="primary"
              shape="circle"
              size="large"
              icon={streaming ? <ComposerStopIcon /> : <ComposerSendIcon />}
              aria-label={streaming ? "停止回答" : "发送问题"}
              disabled={!streaming && !question.trim()}
              onClick={() => void sendQuestion()}
            />
          </div>
        </div>
      </section>
    </div>
  );
}
