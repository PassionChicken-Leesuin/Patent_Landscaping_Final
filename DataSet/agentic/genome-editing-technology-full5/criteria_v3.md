# 도메인 판단 기준서 — Genome Editing Technology

## 도메인 정의
Genome editing technology encompasses methods and tools that enable the precise modification of DNA sequences within the genomes of living organisms. This includes the insertion, deletion, or replacement of genetic material at specific genomic locations, allowing for targeted alterations of genes or genomic regions. The technology is applicable across a wide range of organisms, including plants, animals, and microorganisms, and is used to study gene function, develop genetically modified organisms, and create therapeutic interventions. Key techniques include CRISPR-Cas9, TALENs, and prime editing, which utilize programmable nucleases and guide RNAs to achieve high precision in genome modifications.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the modification of DNA sequences in living organisms through insertion, deletion, or replacement of genetic material at specific genomic locations.
  - 근거: corpus: definition, corpus: task, corpus: technique
- **C2.** The invention must utilize a programmable nuclease or similar tool to target specific genes or genomic regions with high precision.
  - 근거: corpus: technique, corpus: task
- **C3.** The invention must actively perform genome editing across a variety of organisms, including plants, animals, and microorganisms, for purposes such as research, agriculture, or therapeutic development.
  - 근거: corpus: task, corpus: definition
- **C4.** The invention must actively facilitate the study of gene function or the development of genetically modified organisms through genome editing.
  - 근거: corpus: task, corpus: definition

## 분석 대상 특허의 범위
The scope of analysis for genome editing technology includes patents that implement, improve, or provide enabling components or methods specific to genome editing. This encompasses technologies that perform precise DNA modifications, utilize programmable nucleases, or are specific applications of genome editing in research, agriculture, or therapeutics. Excluded are technologies that merely use genome editing outputs or vocabulary for unrelated purposes.

## 범위 결정 (클러스터별 in/out)

- [IN] **CRISPR-Cas9 technology** — CRISPR-Cas9 is a core genome editing technology that enables precise DNA modifications.
- [IN] **gene editing methods** — Gene editing methods that involve precise DNA modifications fall within the domain.
- [CONDITIONAL] **homologous recombination** — In if used for precise genome editing; out if used solely for detection or unrelated applications.
- [IN] **plant genetic engineering** — Plant genetic engineering using genome editing techniques is within the domain.
- [CONDITIONAL] **nucleic acid therapeutics** — In if they involve genome editing technologies; out if they do not specify genome editing techniques.
- [CONDITIONAL] **gene expression modulation** — In if modulation is achieved through genome editing; out if it does not involve direct genome editing techniques.
- [IN] **gene knockout methods** — Gene knockout methods using genome editing technologies are within the domain.
- [CONDITIONAL] **recombinant virus construction** — In if used for genome editing purposes; out if for unrelated vector production.
- [OUT] **high-throughput gene screening** — High-throughput gene screening without direct genome editing involvement is outside the domain.
- [IN] **RNA-targeted editing** — RNA-targeted editing that involves genome editing technologies is within the domain.
- [IN] **gene therapy applications** — Gene therapy applications using genome editing technologies are within the domain.
- [IN] **transgenic plant methods** — Transgenic plant methods using genome editing technologies are within the domain.
- [IN] **RNA-guided endonucleases** — RNA-guided endonucleases are a key component of genome editing technologies.
- [CONDITIONAL] **gene delivery platforms** — In if specific to genome editing; out if for general gene delivery without genome editing.
- [CONDITIONAL] **non-viral vectors** — In if used for genome editing; out if for unrelated gene delivery purposes.

## 제외 기준 (E)

- **E1.** Patents that focus on gene expression modulation technologies that do not involve genome editing are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E2.** Patents involving genetic modification for vector production without direct genome editing are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E3.** Patents discussing nucleic acid-based therapeutics that do not specify genome editing technologies are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E4.** Patents related to detection methods rather than genome editing are excluded.
  - 근거: corpus: suspected_boundary_cases

## 경계 판정 지침

- Patents focusing on gene expression modulation without direct genome editing techniques should be excluded unless they explicitly involve genome editing.
- Patents involving genetic modification for vector production should be excluded unless they specifically pertain to genome editing.
- Patents discussing nucleic acid-based therapeutics should be included only if they specify genome editing technologies.
- Patents related to agricultural applications using CRISPR/Cas9 should be included if they focus on genome editing technology itself.

## 사용자 결정이 필요한 범위 질문

- **Q1. Should patents focusing on gene expression modulation without direct genome editing techniques be included?**
  - 영향: 측정: 풀 표본 60건 중 33건(~55%)의 판정이 넓게/좁게에 따라 갈립니다. This determines whether indirect applications of genome editing are within scope.
  - 선택지: Include if they involve genome editing indirectly., Exclude unless they involve direct genome editing techniques.
  - 현재 가정(미답변 시): Exclude unless they involve direct genome editing techniques.
- **Q3. Should patents discussing nucleic acid-based therapeutics without specific genome editing technologies be included?**
  - 영향: 측정: 풀 표본 60건 중 33건(~55%)의 판정이 넓게/좁게에 따라 갈립니다. This affects the inclusion of therapeutic applications that may not directly involve genome editing.
  - 선택지: Include if they have potential applications in genome editing., Exclude unless they specify genome editing technologies.
  - 현재 가정(미답변 시): Exclude unless they specify genome editing technologies.
- **Q2. Should patents involving genetic modification for vector production be included?**
  - 영향: 측정: 풀 표본 60건 중 32건(~53%)의 판정이 넓게/좁게에 따라 갈립니다. This affects the inclusion of patents that support genome editing indirectly.
  - 선택지: Include if they support genome editing indirectly., Exclude unless they specifically pertain to genome editing.
  - 현재 가정(미답변 시): Exclude unless they specifically pertain to genome editing.
