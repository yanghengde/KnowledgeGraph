import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const BUILD_DIR = "D:/Deepseek/camstar/CamstarSemiOntology/outputs/camstar_presentation_build";
const FINAL_PPTX = "D:/Deepseek/camstar/CamstarSemiOntology/outputs/CamstarOntology_项目介绍_三页版.pptx";
const OVERVIEW_IMAGE = `${BUILD_DIR}/deployed_overview.png`;
const QUERY_IMAGE = `${BUILD_DIR}/deployed_query_builder.png`;
const RENDER_DIR = `${BUILD_DIR}/deck_renders`;

const C = {
  canvas: "#FFFFFF",
  ink: "#061826",
  muted: "#52616B",
  rule: "#B8BCC4",
  panel: "#EDEDED",
  accent: "#00C7A7",
  accentBlue: "#3D8DFF",
  pale: "#EAF7F5",
};

const FONT = "Microsoft YaHei";

async function imageBytes(path) {
  const bytes = await fs.readFile(path);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function addText(slide, name, text, position, style = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = {
    fontSize: style.fontSize ?? 22,
    bold: style.bold ?? false,
    color: style.color ?? C.ink,
    typeface: style.typeface ?? FONT,
    alignment: style.alignment ?? "left",
    verticalAlignment: style.verticalAlignment ?? "top",
    autoFit: style.autoFit ?? "none",
    wrap: "square",
    ...style,
  };
  return box;
}

function addRule(slide, name, left, top, width, color = C.rule, weight = 1) {
  return slide.shapes.add({
    geometry: "line",
    name,
    position: { left, top, width, height: 0 },
    fill: "none",
    line: { style: "solid", fill: color, width: weight },
  });
}

function addFooter(slide, value) {
  addText(
    slide,
    `footer-${value}`,
    value,
    { left: 1184, top: 659, width: 55, height: 25 },
    { fontSize: 14, color: C.muted, alignment: "right", verticalAlignment: "bottom" },
  );
}

function setNotes(slide, talkTrack, sources) {
  slide.speakerNotes.textFrame.setText(
    `${talkTrack}\n\n[Sources]\n${sources.map((source) => `- ${source}`).join("\n")}`,
  );
  slide.speakerNotes.setVisible(true);
}

function addHeroImage(slide, bytes, alt, crop) {
  slide.shapes.add({
    geometry: "roundRect",
    name: `${alt}-backing`,
    position: { left: 658.17, top: 41.62, width: 581.6, height: 588.14 },
    fill: C.pale,
    line: { style: "solid", fill: C.rule, width: 1 },
    borderRadius: 14,
  });
  slide.images.add({
    blob: bytes,
    contentType: "image/png",
    alt,
    fit: "cover",
    crop,
    geometry: "roundRect",
    borderRadius: 14,
    position: { left: 658.17, top: 41.62, width: 581.6, height: 588.14 },
  });
}

function addQuadrant(slide, index, title, body, left, top) {
  addText(
    slide,
    `capability-number-${index}`,
    `0${index}`,
    { left, top, width: 56, height: 30 },
    { fontSize: 20, bold: true, color: C.accentBlue },
  );
  addText(
    slide,
    `capability-title-${index}`,
    title,
    { left: left + 66, top: top - 4, width: 470, height: 40 },
    { fontSize: 28, bold: true, color: C.ink },
  );
  addText(
    slide,
    `capability-body-${index}`,
    body,
    { left: left + 66, top: top + 48, width: 470, height: 92 },
    { fontSize: 19, color: C.muted, autoFit: "shrinkText" },
  );
}

async function main() {
  await fs.mkdir(RENDER_DIR, { recursive: true });
  const overview = await imageBytes(OVERVIEW_IMAGE);
  const query = await imageBytes(QUERY_IMAGE);

  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  // Slide 1 — Codex Grid slide-08 hierarchy: title band + left message + right hero.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.canvas;
    addText(
      slide,
      "cover-title",
      "CamstarOntology",
      { left: 41.33, top: 36.12, width: 605, height: 96 },
      { fontSize: 67, bold: true, color: C.ink, typeface: "Arial" },
    );
    addText(
      slide,
      "cover-kicker",
      "SIEMENS OPCENTER MES · 本体知识图谱",
      { left: 41.33, top: 182, width: 570, height: 30 },
      { fontSize: 18, bold: true, color: C.accent },
    );
    addText(
      slide,
      "cover-message",
      "让复杂的 MES 模型\n变成可探索的知识图谱",
      { left: 41.33, top: 225, width: 570, height: 142 },
      { fontSize: 38, bold: true, color: C.ink },
    );
    addText(
      slide,
      "cover-summary",
      "统一物理 Schema、本体关系、Neo4j 图存储与 G6 交互探索，帮助团队快速理解 Camstar 业务对象及其连接方式。",
      { left: 41.33, top: 405, width: 560, height: 132 },
      { fontSize: 23, color: C.muted, autoFit: "shrinkText" },
    );
    addText(
      slide,
      "cover-evidence",
      "593 类  ·  8337 属性  ·  1592 关系",
      { left: 41.33, top: 573, width: 560, height: 38 },
      { fontSize: 21, bold: true, color: C.accentBlue },
    );
    addHeroImage(slide, overview, "CamstarOntology 全景图谱界面");
    addFooter(slide, "01");
    setNotes(
      slide,
      "开场先说明平台的沟通目标：把原本分散在 Camstar 物理表、字段和外键中的模型知识，转化为可搜索、可追踪、可解释的知识图谱。右侧是真实部署系统的全景图。",
      [
        "项目仓库 README.md（本地事实来源，2026-08-06）",
        "部署系统 http://172.17.119.98:5050/（界面截图与统计，采集于 2026-08-06）",
      ],
    );
  }

  // Slide 2 — Codex Grid slide-13 hierarchy: one title + four equal evidence regions.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.canvas;
    addText(
      slide,
      "capabilities-title",
      "四层能力构成本体建模与使用闭环",
      { left: 41.33, top: 36.12, width: 1197.33, height: 72 },
      { fontSize: 48, bold: true, color: C.ink },
    );
    addText(
      slide,
      "capabilities-subtitle",
      "从数据库事实出发，经过规范化建模和自动验证，最终服务于图谱探索与智能协作。",
      { left: 41.33, top: 118, width: 1120, height: 36 },
      { fontSize: 21, color: C.muted },
    );
    addRule(slide, "horizontal-rule", 41.33, 406, 1197, C.rule, 1);
    slide.shapes.add({
      geometry: "line",
      name: "vertical-rule",
      position: { left: 640, top: 190, width: 0, height: 430 },
      fill: "none",
      line: { style: "solid", fill: C.rule, width: 1 },
    });
    addQuadrant(
      slide,
      1,
      "物理结构对齐",
      "以 Database_Tables.csv 与 Database_Fields.csv 为唯一事实来源，统一 CDO、字段类型和外键。",
      50,
      223,
    );
    addQuadrant(
      slide,
      2,
      "规范化本体建模",
      "普通字段映射为数据属性，外键统一映射为 Navigation，并补齐跨模块关系与双语说明。",
      665,
      223,
    );
    addQuadrant(
      slide,
      3,
      "验证与图数据库加载",
      "自动检查缺失属性、类型不一致与关系遗漏，再通过批量 UNWIND 同步到 Neo4j。",
      50,
      441,
    );
    addQuadrant(
      slide,
      4,
      "交互探索与智能协作",
      "支持搜索、邻域高亮、节点详情与查询构建；Graph‑RAG 通过 @实体提供上下文问答。",
      665,
      441,
    );
    addFooter(slide, "02");
    setNotes(
      slide,
      "这一页强调系统不是单纯的图谱展示。它从物理 Schema 对齐开始，经由本体建模、校验和 Neo4j 加载形成治理闭环，再向上提供图谱探索、SQL 查询构建和 Graph-RAG 协作能力。",
      [
        "项目仓库 AGENTS.md 与 README.md（流程与功能事实来源，2026-08-06）",
        "部署系统 http://172.17.119.98:5050/（功能核验，2026-08-06）",
      ],
    );
  }

  // Slide 3 — Codex Grid slide-08 hierarchy reused with a different evidence silhouette.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.canvas;
    addText(
      slide,
      "workflow-title",
      "从节点理解到查询生成",
      { left: 41.33, top: 36.12, width: 580, height: 72 },
      { fontSize: 46, bold: true, color: C.ink },
    );
    addText(
      slide,
      "workflow-stat",
      "54 / 96",
      { left: 41.33, top: 205, width: 250, height: 66 },
      { fontSize: 52, bold: true, color: C.accent },
    );
    addText(
      slide,
      "workflow-stat-label",
      "Container 图上邻居 / 完整关系",
      { left: 41.33, top: 275, width: 460, height: 34 },
      { fontSize: 20, bold: true, color: C.muted },
    );
    addRule(slide, "workflow-rule", 41.33, 329, 548, C.rule, 1);
    addText(
      slide,
      "workflow-step-1",
      "01  搜索与聚焦",
      { left: 41.33, top: 354, width: 520, height: 34 },
      { fontSize: 24, bold: true, color: C.ink },
    );
    addText(
      slide,
      "workflow-step-1-body",
      "按技术名或中文名定位业务对象，立即突出相关节点。",
      { left: 41.33, top: 390, width: 540, height: 50 },
      { fontSize: 19, color: C.muted },
    );
    addText(
      slide,
      "workflow-step-2",
      "02  查看属性与关系",
      { left: 41.33, top: 458, width: 520, height: 34 },
      { fontSize: 24, bold: true, color: C.ink },
    );
    addText(
      slide,
      "workflow-step-2-body",
      "识别字段类型、Navigation 目标、入向引用与出向引用。",
      { left: 41.33, top: 494, width: 540, height: 50 },
      { fontSize: 19, color: C.muted },
    );
    addText(
      slide,
      "workflow-step-3",
      "03  生成查询骨架",
      { left: 41.33, top: 562, width: 520, height: 34 },
      { fontSize: 24, bold: true, color: C.ink },
    );
    addText(
      slide,
      "workflow-step-3-body",
      "选择对象并验证 JOIN 路径，生成 Oracle / SQL Server SQL。",
      { left: 41.33, top: 598, width: 560, height: 42 },
      { fontSize: 19, color: C.muted },
    );
    addHeroImage(
      slide,
      query,
      "查询构建器与 Container 关系聚焦界面",
      { left: 0, top: 0, right: 0.35, bottom: 0 },
    );
    addFooter(slide, "03");
    setNotes(
      slide,
      "用 Container 作为示例演示完整操作：先搜索并聚焦节点，打开详情查看属性与 Navigation 关系，再进入查询构建器选择对象、验证物理关联并生成 SQL 骨架。",
      [
        "部署系统 http://172.17.119.98:5050/（Container 详情与查询构建器截图，采集于 2026-08-06）",
      ],
    );
  }

  for (const [index, slide] of presentation.slides.items.entries()) {
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(`${RENDER_DIR}/slide-${index + 1}.png`, new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(`${RENDER_DIR}/slide-${index + 1}.layout.json`, await layout.text(), "utf8");
  }

  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(`${BUILD_DIR}/deck-montage.webp`, new Uint8Array(await montage.arrayBuffer()));

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);
  console.log(FINAL_PPTX);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
