# 도메인 판단 기준서 — Genome Editing Technology

## 도메인 정의
Genome Editing Technology encompasses methods and tools that enable precise modifications to the genetic material of living organisms. This includes technologies that allow for the insertion, deletion, or replacement of specific DNA segments, targeting specific genes or genomic regions with high accuracy. The technology facilitates the study of gene function by enabling gene knockout or modification and is applicable to a wide range of organisms, including plants, animals, and microorganisms.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the precise alteration of DNA sequences in living organisms.
  - 근거: corpus: definition, corpus: task, corpus: technique
- **C2.** The invention must allow for the insertion, deletion, or replacement of specific DNA segments.
  - 근거: corpus: definition, corpus: technique
- **C3.** The invention must be capable of targeting specific genes or genomic regions with high accuracy.
  - 근거: corpus: task, corpus: technique
- **C4.** The invention must facilitate the study of gene function by enabling gene knockout or modification.
  - 근거: corpus: task, corpus: technique
- **C5.** The invention must be applicable to a wide range of organisms, including plants, animals, and microorganisms.
  - 근거: corpus: task, corpus: technique
- **C6.** The invention must involve a genome editing tool or method, such as CRISPR, TALENs, or prime editing.
  - 근거: corpus: technique, corpus: definition

## 분석 대상 특허의 범위
The scope of analysis for Genome Editing Technology includes patents that implement, improve, or provide enabling components, methods, or materials specific to genome editing. This encompasses inventions that perform precise genetic modifications, target specific genomic regions, or facilitate gene function studies across various organisms. Patents that merely use genome editing outputs or vocabulary for unrelated purposes are excluded.

## 범위 결정 (클러스터별 in/out)

- [IN] **CRISPR-Cas9 systems** — CRISPR-Cas9 systems are a core technology for genome editing, enabling precise DNA modifications.
- [IN] **gene editing methods** — Gene editing methods that allow for precise DNA alterations are central to genome editing technology.
- [IN] **nuclease-based editing** — Nuclease-based editing involves tools like CRISPR and TALENs, which are essential for genome editing.
- [IN] **plant genome modification** — Plant genome modification is a specific application of genome editing technology.
- [IN] **base editing tools** — Base editing tools are a form of genome editing that allows for precise nucleotide changes.
- [IN] **gene delivery systems** — Gene delivery systems are enabling technologies specific to the application of genome editing tools.
- [CONDITIONAL] **anti-CRISPR proteins** — Anti-CRISPR proteins are in scope if they are specifically designed to regulate or enhance genome editing processes.
- [CONDITIONAL] **DNA methylation editing** — DNA methylation editing is in scope if it involves genome editing tools or methods for precise epigenetic modifications.
- [OUT] **genetic variant analysis** — Genetic variant analysis does not involve the direct modification of DNA sequences, which is required for genome editing.
- [IN] **targeted mutagenesis** — Targeted mutagenesis involves precise DNA modifications, aligning with genome editing tasks.
- [IN] **gene knockout methods** — Gene knockout methods are a fundamental application of genome editing technology.
- [CONDITIONAL] **homologous recombination** — Homologous recombination is in scope if used in conjunction with genome editing tools for precise DNA modifications.
- [OUT] **transgene expression enhancement** — Transgene expression enhancement does not involve direct genome editing tasks.
- [OUT] **protein engineering** — Protein engineering does not involve the direct modification of DNA sequences.
- [CONDITIONAL] **genetic engineering applications** — Genetic engineering applications are in scope if they specifically involve genome editing tools or methods.

## 제외 기준 (E)

- **E1.** Patents that involve genetic analysis or diagnostics without direct DNA modification are excluded.
  - 근거: corpus: boundary_case
- **E2.** Patents that enhance gene expression without involving genome editing tools or methods are excluded.
  - 근거: corpus: boundary_case
- **E3.** Patents related to protein engineering without direct genome editing involvement are excluded.
  - 근거: corpus: boundary_case

## 경계 판정 지침

- Patents related to anti-CRISPR proteins are in scope if they are specifically designed to regulate or enhance genome editing processes.
- DNA methylation editing patents are in scope if they involve genome editing tools or methods for precise epigenetic modifications.
- Homologous recombination patents are in scope if used in conjunction with genome editing tools for precise DNA modifications.
- Genetic engineering applications are in scope if they specifically involve genome editing tools or methods.
