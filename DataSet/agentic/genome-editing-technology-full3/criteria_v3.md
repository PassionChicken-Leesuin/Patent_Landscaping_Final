# 도메인 판단 기준서 — Genome Editing Technology

## 도메인 정의
Genome Editing Technology encompasses techniques and tools that enable the precise alteration of DNA sequences within the genomes of living organisms. This includes the ability to insert, delete, or replace specific DNA segments, allowing for targeted modifications at specific genomic loci. The technology must facilitate the study and manipulation of gene function, including gene knockout or modification, and be applicable across a wide range of organisms, such as plants, animals, and microorganisms. The core functionality involves the use of programmable nucleases or other molecular tools to achieve high accuracy in targeting and editing specific genes or genomic regions.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the precise alteration of DNA sequences in living organisms through insertion, deletion, or replacement of specific DNA segments.
  - 근거: corpus: definition, corpus: task, corpus: technique
- **C2.** The invention must utilize a programmable nuclease or similar molecular tool to target specific genes or genomic regions with high accuracy.
  - 근거: corpus: technique, corpus: task
- **C3.** The invention must facilitate the study or manipulation of gene function, such as through gene knockout or modification.
  - 근거: corpus: task, corpus: technique
- **C4.** The invention must be applicable to a wide range of organisms, including plants, animals, and microorganisms.
  - 근거: corpus: task, corpus: technique
- **C5.** The invention must enable direct writing of new genetic information into a targeted DNA site, indicative of prime editing.
  - 근거: corpus: definition, corpus: technique

## 분석 대상 특허의 범위
The scope of analysis for Genome Editing Technology includes patents that describe methods, tools, or applications specifically designed for the precise modification of genetic material in living organisms. This encompasses technologies that enable targeted gene editing, such as CRISPR-Cas9, TALENs, and prime editing, and their applications in various fields including medicine, agriculture, and biotechnology. Patents that focus on enabling technologies, such as delivery systems for genome editing tools, are also within scope if they are specifically designed for genome editing purposes.

## 범위 결정 (클러스터별 in/out)

- [IN] **CRISPR-Cas9 technology** — CRISPR-Cas9 technology is a core genome editing tool that enables precise DNA modifications, fitting the domain's defining tasks.
- [IN] **gene editing methods** — Gene editing methods that involve precise DNA sequence alterations are central to the domain of genome editing technology.
- [OUT] **homologous recombination** — Homologous recombination is not explicitly linked to genome editing in the evidence provided and lacks specific support for inclusion.
- [IN] **gene knockout methods** — Gene knockout methods are a form of genome editing that involves precise gene function manipulation, fitting the domain's criteria.
- [CONDITIONAL] **gene therapy applications** — Gene therapy applications are in scope if they involve direct genome editing techniques to modify genetic material for therapeutic purposes.
- [CONDITIONAL] **plant genetic engineering** — Plant genetic engineering is in scope if it involves precise genome editing techniques such as CRISPR or prime editing, rather than general genetic modification.
- [IN] **RNA-guided gene editing** — RNA-guided gene editing, such as CRISPR, is a key technology for precise genome modifications, fitting the domain's criteria.
- [IN] **genome engineering applications** — Applications that involve precise genome engineering techniques are within the scope of genome editing technology.
- [CONDITIONAL] **nucleic acid therapeutics** — Nucleic acid therapeutics are in scope if they involve genome editing techniques to achieve therapeutic outcomes.
- [CONDITIONAL] **viral gene editing** — Viral gene editing is in scope if it involves precise genome editing techniques rather than general viral manipulation.

## 제외 기준 (E)

- **E1.** Patents that focus solely on gene expression modulation without direct genome editing methods are excluded.
  - 근거: corpus: boundary_case, patent-pool: suspected_boundary_cases
- **E2.** Patents related to vector production without direct genome editing techniques are excluded.
  - 근거: patent-pool: suspected_boundary_cases
- **E3.** Patents discussing nucleic acid-based therapeutics focusing on RNA interference are excluded as they do not perform genome editing tasks.
  - 근거: patent-pool: suspected_boundary_cases
- **E4.** Genetic modification techniques that do not involve precise editing like CRISPR are excluded as they do not meet the domain's criteria for precision.
  - 근거: patent-pool: suspected_boundary_cases
- **E5.** Patents focusing on detection methods rather than genome editing are excluded.
  - 근거: patent-pool: suspected_boundary_cases

## 경계 판정 지침

- Patents focusing on gene expression modulation without direct genome editing methods should be excluded, as seen in 'The multi-functional gene expression platform of protocatechuic acid regulation and its application'.
- Patents related to vector production without direct genome editing techniques, such as 'Method for producing adenovirus vector', should be excluded.
- Nucleic acid-based therapeutics must involve specific genome editing technologies to be included, otherwise, they are excluded as in 'Nucleic acid-based therapeutics'.
- Genetic modification for agricultural applications must involve precise genome editing techniques, such as CRISPR or prime editing, to be included, otherwise, they are excluded as in 'Method for preparing tomato material with high lycopene content'.
- Detection methods without direct genome editing involvement, such as 'Method for detecting the antibiotic resistance gene blavim-2', should be excluded.
- Plant genetic engineering patents that do not explicitly mention CRISPR or prime editing should be evaluated for the presence of precise genome editing techniques to determine inclusion.
- Prime editing applications should be included if they demonstrate the ability to directly write new genetic information into targeted DNA sites.
