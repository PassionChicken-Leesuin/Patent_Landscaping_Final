import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const ROOT = nodeRepl.cwd;
const RAW_PATH = path.join(ROOT, "휴머노이드문제", "휴머노이드특허_Raw.xlsx");
const GOLD_PATH = path.join(ROOT, "DataSet", "humanoid", "goldset_v1_1.csv");
const AUDIT_PATH = path.join(
  ROOT,
  "DataSet",
  "agentic",
  "humanoid-robot-commercialization-technologies-goldset-v1",
  "judge",
  "audit.jsonl",
);
const OUTPUT_DIR = path.join(ROOT, "outputs", "gold_v1_1_final");
const PREVIEW_DIR = path.join(ROOT, "temp", "gold_v1_1_previews");
const OUTPUT_PATH = path.join(
  OUTPUT_DIR,
  "휴머노이드_Gold_v1_1_패밀리대표_3323건.xlsx",
);

const H_LABELS = {
  H1: "직접 휴머노이드",
  H2: "로봇손·파지·촉각",
  H3: "매니퓰레이션 학습·제어",
  H4: "균형·보행·자세",
  H5: "액추에이터·감속기·관절",
  H6: "로봇비전·VLA·모방학습",
  H7: "텔레옵·Sim-to-Real·데이터",
  H8: "인간협업 안전",
};

const H_ORDER = Object.keys(H_LABELS);
const CRITERIA_TO_H = {
  C1: "H4",
  C2: "H2",
  C3: "H3",
  C4: "H5",
  C5: "H6",
  C6: "H8",
  C7: "H6",
};

function cleanHeader(value) {
  return String(value ?? "").replace(/^\uFEFF/, "").trim();
}

function boolValue(value) {
  return String(value ?? "").trim().toLowerCase() === "true";
}

function colName(indexZeroBased) {
  let n = indexZeroBased + 1;
  let s = "";
  while (n > 0) {
    const r = (n - 1) % 26;
    s = String.fromCharCode(65 + r) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

function textOf(rawRow, rawHeader) {
  const useful = [
    "발명의 명칭",
    "발명의 명칭-번역문",
    "요약",
    "요약-번역문",
    "대표청구항",
    "대표청구항-번역문",
    "독립청구항[KR,JP,US,CN,EP,IN]",
    "독립청구항-번역문[JP,US,CN,EP]",
    "AI 요약[KR,US,JP,CN,EP,PCT,TW]",
    "기술분야 요약[KR,US,JP,CN,EP,PCT,TW]",
    "해결과제 요약[KR,US,JP,CN,EP,PCT,TW]",
    "해결수단 요약[KR,US,JP,CN,EP,PCT,TW]",
    "특징 요약[KR,US,JP,CN,EP,PCT,TW]",
    "효과 요약[KR,US,JP,CN,EP,PCT,TW]",
  ];
  const index = Object.fromEntries(rawHeader.map((h, i) => [h, i]));
  return useful
    .map((h) => rawRow[index[h]])
    .filter((v) => v !== null && v !== undefined)
    .join(" ")
    .toLowerCase();
}

function addStrongSignalLabels(labels, text, goldRow) {
  if (
    goldRow.label_v1 === "T1_auto" ||
    /\bhumanoid\b|anthropomorphic|human[- ]like robot|\bbiped(?:al)?\b|two[- ]legged|휴머노이드|인간형|이족/.test(
      text,
    )
  ) {
    labels.add("H1");
  }
  if (
    /\b(robotic hand|robot hand|dexterous hand|multi[- ]finger|gripper|grasp(?:ing)?|tactile|finger mechanism|in[- ]hand manipulation)\b|로봇손|다지|그리퍼|파지|촉각|손가락/.test(
      text,
    )
  ) {
    labels.add("H2");
  }
  if (
    /\b(manipulat(?:e|ion|or)|motion planning|trajectory planning|impedance control|force control|reinforcement learning|learning from demonstration)\b|매니퓰레이션|조작 학습|동작 계획|궤적 계획|임피던스 제어|힘 제어|강화학습/.test(
      text,
    )
  ) {
    labels.add("H3");
  }
  if (
    /\b(zero moment point|zmp|whole[- ]body|balance control|posture control|gait|walking|locomotion|fall detection|fall recovery|legged robot)\b|전신 제어|균형 제어|보행|자세 제어|낙상|다족|사족|휠레그/.test(
      text,
    )
  ) {
    labels.add("H4");
  }
  if (
    /\b(qdd|quasi[- ]direct drive|series elastic actuator|sea|variable stiffness actuator|vsa|backdriv(?:e|able)|actuator|reducer|gearbox|robotic joint|joint module)\b|준직접구동|직렬탄성|가변강성|액추에이터|감속기|관절 모듈|구동계/.test(
      text,
    )
  ) {
    labels.add("H5");
  }
  if (
    /\b(vision[- ]language[- ]action|vla|imitation learning|learning from demonstration|robot vision|visual perception|grasp perception|pose estimation|foundation model)\b|비전 언어 행동|모방학습|시연학습|로봇 비전|파지 인식|자세 추정|파운데이션 모델/.test(
      text,
    )
  ) {
    labels.add("H6");
  }
  if (
    /\b(tele[- ]?operation|telemanipulation|master[- ]slave|remote manipulation|remote operation|sim[- ]to[- ]real|domain randomi[sz]ation|synthetic data|simulation[- ]based learning|demonstration data|training data)\b|원격조작|마스터.?슬레이브|시연 데이터|합성 데이터|도메인 무작위화|시뮬레이션 기반 학습/.test(
      text,
    )
  ) {
    labels.add("H7");
  }
  if (
    /\b(human[- ]robot collaboration|collaborative robot|collision detection|contact detection|speed and separation|safety envelope|power and force limiting|human coexistence)\b|인간.?로봇 협업|협동로봇|충돌 감지|접촉 감지|안전 거리|접촉력 제한|인간 공존/.test(
      text,
    )
  ) {
    labels.add("H8");
  }
}

function technicalClassification(goldRow, audit, rawText) {
  if (!boolValue(goldRow.gold_v1_1)) {
    const code = exclusionCode(goldRow, audit, rawText);
    return `비대상(${code})`;
  }

  const labels = new Set();
  for (const criterion of audit?.matched_criteria ?? []) {
    const mapped = CRITERIA_TO_H[criterion];
    if (mapped) labels.add(mapped);
  }
  addStrongSignalLabels(labels, rawText, goldRow);

  // Manual rescues are all T1/OEM or direct-platform cases in gold v1.1.
  if (goldRow.adjust?.startsWith("구제:")) labels.add("H1");

  // Every positive must be classifiable. This fallback is only reached when the
  // final included decision is broader than the recorded criterion list.
  if (labels.size === 0) labels.add("H3");

  return H_ORDER.filter((h) => labels.has(h))
    .map((h) => `${h} ${H_LABELS[h]}`)
    .join("; ");
}

function exclusionCode(goldRow, audit, text) {
  if (goldRow.adjust?.includes("산업용 주변기술")) return "E1";
  if (goldRow.adjust?.includes("오탐사전")) return "E7";
  if (
    /\b(surgical|surgery|laparoscop|catheter|medical procedure|operating room)\b|수술|시술|카테터/.test(
      text,
    )
  ) {
    return "E2";
  }
  if (
    /\b(exoskeleton|prosthe(?:sis|tic)|orthosis|rehabilitation|wearable assist)\b|외골격|의지|의수|보행보조|재활/.test(
      text,
    ) &&
    !/\brecycling\b/.test(text)
  ) {
    return "E3";
  }
  if (
    /\b(robot cleaner|cleaning robot|vacuum cleaner|floor cleaning|lawn mower|mowing robot)\b|청소 로봇|로봇 청소기|바닥 청소|잔디깎/.test(
      text,
    )
  ) {
    return "E4";
  }
  if (
    /\b(agv|automated guided vehicle|warehouse workflow|palleti[sz]|conveyor|sortation|material transport|logistics transport)\b|물류 반송|팔레타이징|컨베이어|창고 워크플로|분류 설비/.test(
      text,
    )
  ) {
    return "E5";
  }
  if (
    /\b(toy robot|robot toy|virtual robot|robot virtualization|entertainment device|animatronic)\b|로봇 완구|장난감 로봇|가상 로봇|애니매트로닉/.test(
      text,
    )
  ) {
    return "E6";
  }
  if (
    /\b(welding|painting line|wafer|semiconductor transfer|smt|machine tool|industrial process|assembly line|jig|offline programming|olp)\b|용접|도장 라인|웨이퍼|반도체 반송|공작기계|조립 라인|교시 ui|캘리브레이션/.test(
      text,
    )
  ) {
    return "E1";
  }
  if ((audit?.violated_exclusions ?? []).includes("E1")) return "E1";
  if ((audit?.violated_exclusions ?? []).includes("E2")) return "E0";
  return "E0";
}

function reasonFor(goldRow, audit, classification, rawText) {
  const included = boolValue(goldRow.gold_v1_1);
  if (included) {
    const shortLabels = classification
      .split("; ")
      .map((x) => x.split(" ").slice(0, 2).join(" "))
      .join(" / ");
    if (goldRow.adjust?.startsWith("구제:")) {
      return `포함(수동 구제): ${shortLabels}. 사례매핑과 OEM/직접 플랫폼 원칙에 따라 gold v1.1에서 최종 포함.`;
    }
    if (classification.includes("H1 ")) {
      return `포함: ${shortLabels}. 휴머노이드 직접 신호 또는 완제품 플랫폼 계열이며 관련 코어 기술을 청구.`;
    }
    return `포함: ${shortLabels}. 특정 공정 전용이 아닌 휴머노이드 이전가능 코어 기술로 판정.`;
  }

  const code = classification.match(/\((E\d)\)/)?.[1] ?? "E0";
  const reasonByCode = {
    E0: "휴머노이드 상용화 핵심 기능 또는 이전가능 코어 기술이 확인되지 않음",
    E1: "특정 산업 공정·설비 또는 일반 제어/교시/검증 주변기술에 한정",
    E2: "수술·의료 시술 전용 기술로 청구 범위가 한정",
    E3: "착용형 외골격·의지·재활 보조 자체가 목적",
    E4: "바닥청소·잔디깎기 등 청소 전용 기능에 한정",
    E5: "AGV·컨베이어·팔레타이징 등 물류 반송/워크플로 전용",
    E6: "완구·애니매트로닉 또는 로봇 실체 없는 소프트웨어/서비스",
    E7: "밸런서·NC·recycling 등 오탐 어휘 또는 응용례 나열로 인한 비도메인",
  };
  if (goldRow.adjust) {
    return `제외(${code}, v1.1 수동 조정): ${reasonByCode[code]}.`;
  }
  return `제외(${code}): ${reasonByCode[code]}.`;
}

function widthFor(header) {
  if (header === "gold_label") return 11;
  if (header === "기술분류") return 38;
  if (header === "판정이유") return 72;
  if (/발명의 명칭/.test(header)) return 32;
  if (/요약|청구항|문헌번호|메모/.test(header)) return 48;
  if (/출원인|발명자|권리자/.test(header)) return 28;
  if (/링크/.test(header)) return 32;
  if (/CPC|IPC/.test(header)) return 24;
  if (/번호|ID|key/i.test(header)) return 18;
  if (/일$|날짜/.test(header)) return 12;
  if (/국가|국적|코드|종류|상태|유무|관련도|관심/.test(header)) return 12;
  if (/수$/.test(header)) return 10;
  return 18;
}

async function main() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });

  const rawWb = await SpreadsheetFile.importXlsx(await fs.readFile(RAW_PATH));
  const rawWs = rawWb.worksheets.getItem("다운로드");
  const rawValues = await rawWs.getRange("A1:BO3758").values;
  const rawHeader = rawValues[0].map(cleanHeader);
  const rawRows = rawValues.slice(1);
  if (rawHeader.length !== 67 || rawRows.length !== 3757) {
    throw new Error(
      `Raw shape mismatch: expected 3757x67, got ${rawRows.length}x${rawHeader.length}`,
    );
  }

  const rawIndex = Object.fromEntries(rawHeader.map((h, i) => [h, i]));
  const rawByApplication = new Map();
  for (const row of rawRows) {
    const key = String(row[rawIndex["출원번호"]] ?? "").trim();
    if (rawByApplication.has(key)) {
      throw new Error(`Duplicate application number in Raw: ${key}`);
    }
    rawByApplication.set(key, row);
  }

  const goldText = await fs.readFile(GOLD_PATH, "utf8");
  const goldWb = await Workbook.fromCSV(goldText);
  const goldWs = goldWb.worksheets.getItemAt(0);
  const goldValues = await goldWs.getRange("A1:O3324").values;
  const goldHeader = goldValues[0].map(cleanHeader);
  const goldRows = goldValues.slice(1).map((row) =>
    Object.fromEntries(goldHeader.map((h, i) => [h, row[i]])),
  );
  if (goldRows.length !== 3323) {
    throw new Error(`Gold row mismatch: expected 3323, got ${goldRows.length}`);
  }

  const auditRows = (await fs.readFile(AUDIT_PATH, "utf8"))
    .trim()
    .split(/\r?\n/)
    .map(JSON.parse);
  const auditById = new Map(auditRows.map((r) => [String(r.record_id), r]));
  if (auditById.size !== 3323) {
    throw new Error(`Audit row mismatch: expected 3323, got ${auditById.size}`);
  }

  const appended = ["gold_label", "기술분류", "판정이유"];
  const outputHeader = [...rawHeader, ...appended];
  const outputRows = [];
  const techCounts = Object.fromEntries(H_ORDER.map((h) => [h, 0]));
  const exclusionCounts = {};
  const sourceFamilies = new Set();
  let positiveCount = 0;
  let adjustmentCount = 0;

  for (const goldRow of goldRows) {
    const id = String(goldRow.record_id ?? "").trim();
    const rawRow = rawByApplication.get(id);
    if (!rawRow) throw new Error(`Raw match not found for record_id ${id}`);

    const rawFamily = String(rawRow[rawIndex["WIPS패밀리 ID"]] ?? "").trim();
    const goldFamily = String(goldRow["WIPS패밀리 ID"] ?? "").trim();
    if (rawFamily !== goldFamily) {
      throw new Error(
        `Family mismatch for ${id}: Raw=${rawFamily}, gold=${goldFamily}`,
      );
    }
    if (sourceFamilies.has(rawFamily)) {
      throw new Error(`Duplicate family representative: ${rawFamily}`);
    }
    sourceFamilies.add(rawFamily);

    const audit = auditById.get(id);
    if (!audit) throw new Error(`Audit record not found for ${id}`);
    const rawText = textOf(rawRow, rawHeader);
    const included = boolValue(goldRow.gold_v1_1);
    const classification = technicalClassification(goldRow, audit, rawText);
    const reason = reasonFor(goldRow, audit, classification, rawText);
    const label = included ? 1 : 0;
    if (included) {
      positiveCount += 1;
      for (const h of H_ORDER) {
        if (classification.includes(`${h} `)) techCounts[h] += 1;
      }
    } else {
      const code = classification.match(/\((E\d)\)/)?.[1] ?? "E0";
      exclusionCounts[code] = (exclusionCounts[code] ?? 0) + 1;
    }
    if (goldRow.adjust) adjustmentCount += 1;
    outputRows.push([...rawRow, label, classification, reason]);
  }

  if (positiveCount !== 1246) {
    throw new Error(`Positive count mismatch: expected 1246, got ${positiveCount}`);
  }
  if (sourceFamilies.size !== 3323) {
    throw new Error(
      `Unique family count mismatch: expected 3323, got ${sourceFamilies.size}`,
    );
  }
  if (outputRows.some((r) => r.length !== 70)) {
    throw new Error("Output must contain exactly 70 columns");
  }
  if (
    outputRows.some(
      (r) => r[67] === 1 && !/^H[1-8] /.test(String(r[68] ?? "")),
    )
  ) {
    throw new Error("At least one positive record has no H1-H8 classification");
  }

  const wb = Workbook.create();
  const dataWs = wb.worksheets.add("Gold_v1.1");
  const codeWs = wb.worksheets.add("코드북");
  const finalRow = outputRows.length + 1;

  dataWs.getRange("A1:BR1").values = [outputHeader];
  const chunkSize = 200;
  for (let start = 0; start < outputRows.length; start += chunkSize) {
    const chunk = outputRows.slice(start, start + chunkSize);
    dataWs
      .getRangeByIndexes(start + 1, 0, chunk.length, outputHeader.length)
      .writeValues(chunk);
  }

  const fullRange = dataWs.getRange(`A1:BR${finalRow}`);
  fullRange.format.font = { name: "맑은 고딕", size: 9 };
  fullRange.format.verticalAlignment = "top";
  dataWs.getRange("A1:BR1").format = {
    fill: "#1F4E78",
    font: { name: "맑은 고딕", size: 9, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    rowHeight: 42,
    borders: { preset: "all", style: "thin", color: "#D9E2F3" },
  };
  dataWs.getRange(`BP2:BP${finalRow}`).format = {
    horizontalAlignment: "center",
    verticalAlignment: "center",
    font: { name: "맑은 고딕", size: 9, bold: true },
  };
  dataWs.getRange(`BQ2:BR${finalRow}`).format = {
    fill: "#FFFDF2",
    font: { name: "맑은 고딕", size: 9 },
    verticalAlignment: "top",
    wrapText: true,
  };
  dataWs.getRange(`D2:K${finalRow}`).format.wrapText = true;
  dataWs.getRange(`A2:BR${finalRow}`).format.rowHeight = 54;
  dataWs.getRange(`BP2:BP${finalRow}`).conditionalFormats.add("cellIs", {
    operator: "equal",
    formula: 1,
    format: { fill: "#E2F0D9", font: { bold: true, color: "#006100" } },
  });
  dataWs.getRange(`BP2:BP${finalRow}`).conditionalFormats.add("cellIs", {
    operator: "equal",
    formula: 0,
    format: { fill: "#F2F2F2", font: { color: "#666666" } },
  });

  for (let i = 0; i < outputHeader.length; i += 1) {
    const col = colName(i);
    dataWs.getRange(`${col}1:${col}${finalRow}`).format.columnWidth =
      widthFor(outputHeader[i]);
  }
  dataWs.freezePanes.freezeRows(1);
  dataWs.freezePanes.freezeColumns(5);
  dataWs.showGridLines = false;
  const dataTable = dataWs.tables.add(
    `A1:BR${finalRow}`,
    true,
    "HumanoidGoldV11",
  );
  dataTable.style = "TableStyleMedium2";
  dataTable.showBandedColumns = false;
  dataTable.showFilterButton = true;

  // Codebook sheet
  codeWs.mergeCells("A1:D1");
  codeWs.getRange("A1").values = [
    ["휴머노이드 특허 Gold v1.1 | 코드북·검증표"],
  ];
  codeWs.getRange("A1:D1").format = {
    fill: "#17365D",
    font: { name: "맑은 고딕", size: 16, bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
    rowHeight: 36,
  };
  codeWs.mergeCells("A2:D2");
  codeWs.getRange("A2").values = [
    [
      "판정 단위: WIPS 패밀리 대표 1건 | 원본 67열 보존 + gold_label·기술분류·판정이유 3열 추가",
    ],
  ];
  codeWs.getRange("A2:D2").format = {
    fill: "#D9EAF7",
    font: { name: "맑은 고딕", size: 10, color: "#17365D" },
    rowHeight: 26,
  };

  codeWs.getRange("A4:B10").values = [
    ["검증 항목", "값"],
    ["버전", "gold v1.1 (2026-07-24 확정)"],
    ["패밀리 대표 행 수", 3323],
    ["gold_label=1", 1246],
    ["gold_label=0", 2077],
    ["원본 열 수", 67],
    ["최종 열 수", 70],
  ];
  codeWs.getRange("D4:D10").values = [
    ["Excel 재검산"],
    [""],
    [null],
    [null],
    [null],
    [null],
    [null],
  ];
  codeWs.getRange("D6:D10").formulas = [
    [`=ROWS('Gold_v1.1'!A2:A${finalRow})`],
    [`=COUNTIF('Gold_v1.1'!BP2:BP${finalRow},1)`],
    [`=COUNTIF('Gold_v1.1'!BP2:BP${finalRow},0)`],
    ["=67"],
    ["=COLUMNS('Gold_v1.1'!A1:BR1)"],
  ];
  codeWs.getRange("C4:C10").values = [
    ["판정/산출 기준"],
    ["최종 기준서"],
    ["WIPS패밀리 ID 중복 제거"],
    ["최종 유효특허"],
    ["최종 제외특허"],
    ["Raw.xlsx 전체 열"],
    ["67+3"],
  ];

  codeWs.getRange("A12:D12").merge();
  codeWs.getRange("A12").values = [["KIMM 가치사슬 3축과 최종 기술분류 H1–H8"]];
  codeWs.getRange("A13:D21").values = [
    ["코드", "기술분류", "KIMM 3축", "적용 범위"],
    ["H1", H_LABELS.H1, "통합(H/W·지능·데이터)", "휴머노이드·이족·인간형 본체, 전신 제어, 완제품 플랫폼"],
    ["H2", H_LABELS.H2, "H/W", "다지 손, 그리퍼, 파지, 촉각·힘/토크 센싱, 인핸드 조작"],
    ["H3", H_LABELS.H3, "H/W·지능", "모션 플래닝, 힘·임피던스 제어, 조작 스킬 학습"],
    ["H4", H_LABELS.H4, "H/W", "ZMP, 전신 동역학, 보행, 자세, 낙상 예측·복구"],
    ["H5", H_LABELS.H5, "H/W", "QDD·SEA·VSA, 백드라이버블 관절, 감속기, 경량 구동계"],
    ["H6", H_LABELS.H6, "지능", "로봇 비전, VLA, LfD, 강화학습 조작, 파지용 인식"],
    ["H7", H_LABELS.H7, "데이터", "텔레오퍼레이션, 시연·합성 데이터, 도메인 무작위화, Sim-to-Real"],
    ["H8", H_LABELS.H8, "H/W·지능", "충돌·접촉 감지, 힘·속도 제한, 인간 공존 환경 안전"],
  ];
  codeWs.getRange("F13:G21").values = [
    ["기술코드", "gold_label=1 건수(복수분류)"],
    ...H_ORDER.map((h) => [h, techCounts[h]]),
  ];

  codeWs.getRange("A23:D23").merge();
  codeWs.getRange("A23").values = [["라벨·분류 열 해석"]];
  codeWs.getRange("A24:D28").values = [
    ["열", "값", "의미", "분석 시 사용"],
    ["gold_label", "1", "최종 유효특허", "특허 통계·출원인 분석·클러스터링 기본 모집단"],
    ["gold_label", "0", "최종 제외특허", "오탐·경계 규칙 검증용 대조군"],
    ["기술분류", "H1–H8", "포함 특허 기술축, 세미콜론으로 복수 라벨", "복수 분류를 분리 집계"],
    ["기술분류", "비대상(E0–E7)", "제외특허의 주된 제외 유형", "포함 기술분포 집계에서는 제외"],
  ];

  const rules = [
    ["1", "용도 전용성", "특정 공정·설비·용도가 청구항 한정요소이면 제외; 파지·힘제어·학습·관절 기구 자체면 포함."],
    ["2", "완제품 OEM 3분할", "휴머노이드 라인은 핵심 포함, 4족·legged 일반은 이전가능 포함, 흡착 물류 전용은 제외."],
    ["3", "역방향 구제", "종합 대기업 특허라도 휴머노이드가 명시되면 핵심으로 포함."],
    ["4", "4족 원칙", "4족·다족·휠레그의 전신제어·다리 액추에이터·균형은 포함; 완구 4족만 제외."],
    ["5", "물류 학습 2분할", "파지·조작 스킬 학습은 포함; 팔레타이징 배치·분류 자원할당 등 워크플로 학습은 제외."],
    ["6", "산업용 회색지대", "힘 기반 직접교시·리드스루·학습용 파라미터 튜닝은 포함; OLP·공정검증·교시 UI·캘리브레이션은 제외."],
    ["7", "흡착 3예외", "진공 흡착은 기본 제외. 힘/촉각 피드백, 손가락 하이브리드, 파지품질 학습·물리모델이면 포함."],
    ["8", "소프트 그리퍼", "파지 원리·기구는 포함(약); 유체 배관·허브 등 시스템 패키징은 제외."],
    ["9", "외골격 예외", "원격조작 마스터·학습 데이터 수집용이면 포함; 관절 요소기술 자체를 청구해도 포함."],
    ["10", "안전 판별", "인간 공존 환경의 충돌·접촉·속도·거리 안전만 포함; 물체 이송 안전·설비 기능안전은 제외."],
    ["11", "시뮬레이션 판별", "학습·데이터 생성·Sim-to-Real·튜닝용만 포함; 공정 검증·OLP·설계도구는 제외."],
    ["12", "오탐 어휘 주의", "recycling·load balancing·gravity balancer·pedestrian·가공물 pose 및 응용례 나열을 포함 근거로 쓰지 않음."],
  ];
  codeWs.getRange("A30:D30").merge();
  codeWs.getRange("A30").values = [["Gold v1.1 확정 경계 규칙 12개"]];
  codeWs.getRange("A31:D43").values = [
    ["번호", "규칙", "판정 기준", "결과"],
    ...rules.map(([n, title, rule]) => [n, title, rule, "확정"]),
  ];

  codeWs.getRange("A45:D45").merge();
  codeWs.getRange("A45").values = [["제외 코드"]];
  codeWs.getRange("A46:D54").values = [
    ["코드", "제외 유형", "대표 범위", "비고"],
    ["E0", "기타 비도메인", "휴머노이드 코어 또는 이전가능성 미확인", "일반 비대상"],
    ["E1", "산업 공정·주변기술", "용접·도장·가공·웨이퍼·교시UI·OLP·캘리브레이션", "청구항 전용성 기준"],
    ["E2", "수술·의료", "수술 셋업·카테터·의료 연속체 로봇", "범용 코어는 예외 구제"],
    ["E3", "외골격·재활", "착용 보조·의지·재활 자체 목적", "텔레옵/데이터·관절요소는 예외"],
    ["E4", "청소·잔디", "바닥청소·잔디깎기 전용", "응용례 나열은 제외 근거 아님"],
    ["E5", "물류·반송", "AGV·컨베이어·팔레타이징·분류 워크플로", "조작 스킬 학습은 예외"],
    ["E6", "완구·비실체 SW", "완구·애니매트로닉·가상화/통신 서비스", "실체 코어 미포함"],
    ["E7", "오탐 어휘", "밸런서·NC·recycling·load balancing 등", "문맥 확인 후 제외"],
  ];
  codeWs.getRange("A56:D56").merge();
  codeWs.getRange("A56").values = [["데이터 계보"]];
  codeWs.getRange("A57:D62").values = [
    ["항목", "파일", "역할", "검증 결과"],
    ["원본", "휴머노이드특허_Raw.xlsx", "67개 원본 열", "3,757건"],
    ["최종 라벨", "goldset_v1_1.csv", "패밀리 대표·최종 포함/제외", "3,323건 / 양성 1,246건"],
    ["판정 감사", "judge/audit.jsonl", "C1–C7·E 판정과 rationale", "3,323건"],
    ["최종 규칙", "A2_판정규칙_v1.md", "도메인 소유자 확정 기준", "12개 경계 규칙"],
    ["최종 산출물", path.basename(OUTPUT_PATH), "67+3열 분석용 골드셋", "행·열·라벨·패밀리 검증 통과"],
  ];

  codeWs.getRange("A:A").format.columnWidth = 16;
  codeWs.getRange("B:B").format.columnWidth = 30;
  codeWs.getRange("C:C").format.columnWidth = 30;
  codeWs.getRange("D:D").format.columnWidth = 76;
  codeWs.getRange("E:E").format.columnWidth = 4;
  codeWs.getRange("F:F").format.columnWidth = 14;
  codeWs.getRange("G:G").format.columnWidth = 22;

  for (const range of ["A4:D10", "A13:D21", "F13:G21", "A24:D28", "A31:D43", "A46:D54", "A57:D62"]) {
    codeWs.getRange(range).format = {
      font: { name: "맑은 고딕", size: 10 },
      verticalAlignment: "top",
      wrapText: true,
      borders: { preset: "all", style: "thin", color: "#B4C6E7" },
    };
    codeWs.getRange(range).format.autofitRows();
  }
  for (const range of ["A4:D4", "A13:D13", "F13:G13", "A24:D24", "A31:D31", "A46:D46", "A57:D57"]) {
    codeWs.getRange(range).format = {
      fill: "#4472C4",
      font: { name: "맑은 고딕", size: 10, bold: true, color: "#FFFFFF" },
      verticalAlignment: "center",
      horizontalAlignment: "center",
      wrapText: true,
      borders: { preset: "all", style: "thin", color: "#B4C6E7" },
    };
  }
  for (const range of ["A12:D12", "A23:D23", "A30:D30", "A45:D45", "A56:D56"]) {
    codeWs.getRange(range).format = {
      fill: "#D9E2F3",
      font: { name: "맑은 고딕", size: 11, bold: true, color: "#17365D" },
      verticalAlignment: "center",
      rowHeight: 26,
    };
  }
  codeWs.getRange("A1:G62").format.font = { name: "맑은 고딕" };
  codeWs.freezePanes.freezeRows(3);
  codeWs.showGridLines = false;

  const xlsx = await SpreadsheetFile.exportXlsx(wb);
  await xlsx.save(OUTPUT_PATH);

  const previewDataLeft = await wb.render({
    sheetName: "Gold_v1.1",
    range: "A1:H12",
    scale: 1,
    format: "png",
    headers: true,
  });
  await fs.writeFile(
    path.join(PREVIEW_DIR, "gold_data_left.png"),
    new Uint8Array(await previewDataLeft.arrayBuffer()),
  );
  const previewDataLabels = await wb.render({
    sheetName: "Gold_v1.1",
    range: "BP1:BR14",
    scale: 1,
    format: "png",
    headers: true,
  });
  await fs.writeFile(
    path.join(PREVIEW_DIR, "gold_data_labels.png"),
    new Uint8Array(await previewDataLabels.arrayBuffer()),
  );
  const previewCodebook = await wb.render({
    sheetName: "코드북",
    range: "A1:G62",
    scale: 0.85,
    format: "png",
    headers: false,
  });
  await fs.writeFile(
    path.join(PREVIEW_DIR, "codebook.png"),
    new Uint8Array(await previewCodebook.arrayBuffer()),
  );

  const inspectSummary = await wb.inspect({
    kind: "workbook,sheet,table",
    maxChars: 5000,
    tableMaxRows: 3,
    tableMaxCols: 8,
    tableMaxCellChars: 80,
  });
  const errorScan = await wb.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: "final formula error scan",
    maxChars: 2500,
  });

  console.log(
    JSON.stringify(
      {
        outputPath: OUTPUT_PATH,
        rows: outputRows.length,
        originalColumns: rawHeader.length,
        finalColumns: outputHeader.length,
        positiveCount,
        negativeCount: outputRows.length - positiveCount,
        uniqueFamilies: sourceFamilies.size,
        adjustmentCount,
        techCounts,
        exclusionCounts,
        inspect: inspectSummary.ndjson,
        errorScan: errorScan.ndjson,
      },
      null,
      2,
    ),
  );
}

await main();
