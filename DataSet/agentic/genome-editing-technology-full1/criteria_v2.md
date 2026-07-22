# 도메인 판단 기준서 — Genome Editing Technology

## 도메인 정의
Genome editing technology encompasses methods and tools that enable precise modifications to the genetic material of living organisms. This includes the ability to insert, delete, or replace specific DNA sequences at targeted genomic locations, often using programmable nucleases like CRISPR-Cas9, TALENs, or prime editing systems. The technology must facilitate targeted modifications that can potentially be heritable, and it should include mechanisms to minimize off-target effects, ensuring specificity and efficiency in the editing process.

## 도메인 판단 기준 (C)

- **C1.** The technology must enable precise alteration of DNA sequences in living organisms, allowing for insertion, deletion, or replacement of specific DNA segments.
  - 근거: corpus: CRISPR-Cas9 technology, corpus: gene editing methods, https://en.wikipedia.org/wiki/Genome_editing
- **C2.** The technology should facilitate targeted modifications at specific genomic locations using programmable nucleases or similar tools.
  - 근거: corpus: RNA-guided gene editing, https://en.wikipedia.org/wiki/CRISPR
- **C3.** The technology must be capable of potentially enabling heritable changes through genome editing techniques.
  - 근거: https://en.wikipedia.org/wiki/Germline_engineering, corpus: human germline engineering
- **C4.** The technology should provide mechanisms for minimizing off-target effects during the editing process to ensure specificity and efficiency.
  - 근거: https://en.wikipedia.org/wiki/CRISPR, corpus: Prime editing

## 분석 대상 특허의 범위
The scope of analysis for genome editing technology includes patents that describe methods and tools for precise genetic modifications in living organisms. This encompasses technologies like CRISPR-Cas9, TALENs, and prime editing, which allow for targeted DNA alterations. The scope includes applications in medicine, agriculture, and biotechnology, provided they involve direct genome editing. Patents that focus solely on gene expression modulation, vector production, or therapeutic delivery without direct genome editing are outside this scope.

## 범위 결정 (클러스터별 in/out)

- [IN] **CRISPR-Cas9 technology** — CRISPR-Cas9 is a core genome editing technology that enables precise DNA modifications, fitting the domain's definition.
- [IN] **gene editing methods** — Gene editing methods that involve precise DNA alterations are central to genome editing technology.
- [OUT] **homologous recombination** — Homologous recombination is not primarily associated with programmable nucleases like CRISPR, which are the focus of the domain.
- [IN] **gene knockout methods** — Gene knockout methods involve targeted DNA modifications, which are a key aspect of genome editing technology.
- [OUT] **gene therapy applications** — Gene therapy applications are excluded unless they specifically involve genome editing technologies like CRISPR or TALENs.
- [IN] **plant genetic engineering** — Plant genetic engineering involving direct genome editing techniques like CRISPR is included, as it aligns with the domain's core purpose.
- [IN] **RNA-guided gene editing** — RNA-guided gene editing, such as CRISPR, is a fundamental genome editing technology.
- [OUT] **nucleic acid-based therapeutics** — Nucleic acid-based therapeutics without specific genome editing techniques do not fit the domain's focus on direct DNA modifications.
- [IN] **genome engineering applications** — Applications involving genome engineering that include precise DNA editing are within the domain's scope.
- [IN] **viral gene editing** — Viral gene editing that involves precise genome modifications is included, as it uses genome editing technologies.

## 제외 기준 (E)

- **E1.** Patents focusing on gene expression modulation without direct genome editing are excluded, as they do not perform the defining tasks of genome editing technology.
  - 근거: corpus: suspected_boundary_cases
- **E2.** Patents related to vector production technologies that do not involve direct genome editing are excluded, as they do not perform the defining tasks of genome editing technology.
  - 근거: corpus: suspected_boundary_cases
- **E3.** Patents discussing therapeutic delivery or medical monitoring technologies that do not involve direct genome editing are excluded, as they do not perform the defining tasks of genome editing technology.
  - 근거: corpus: suspected_boundary_cases

## 경계 판정 지침

- Patents focusing on gene expression modulation without direct genome editing, such as 'The multi-functional gene expression platform of protocatechuic acid regulation and its application', should be excluded as they do not involve precise DNA modifications.
- Patents related to vector production, like 'Method for producing adenovirus vector', should be excluded unless they involve direct genome editing techniques.
- Patents discussing nucleic acid-based therapeutics without specific genome editing techniques, such as 'Nucleic acid-based therapeutics', should be excluded as they do not involve direct genome editing.
- Patents related to plant genetic engineering should be included if they involve direct genome editing techniques like CRISPR, as they align with the domain's core purpose.
- Patents involving prime editing should be included as they represent a significant advancement in genome editing technology, despite not being prominently featured in the patent pool.
