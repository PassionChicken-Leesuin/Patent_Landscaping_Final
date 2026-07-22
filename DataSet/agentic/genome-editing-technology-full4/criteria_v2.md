# 도메인 판단 기준서 — Genome Editing Technology

## 도메인 정의
Genome editing technology encompasses methods and tools that enable precise alterations to the DNA sequence of an organism. This includes the insertion, deletion, or modification of specific genes within a genome, allowing for targeted changes without affecting other parts of the genome. The technology must provide mechanisms for delivering the editing components to target cells or tissues and be applicable across a wide range of organisms, including plants, animals, and microorganisms.

## 도메인 판단 기준 (C)

- **C1.** The invention must involve a method or tool that enables the precise alteration of DNA sequences within an organism's genome.
  - 근거: corpus: definition, corpus: technique
- **C2.** The invention must include a mechanism for the insertion, deletion, or modification of specific genes within a genome.
  - 근거: corpus: definition, corpus: technique
- **C3.** The invention must provide a method for delivering genome editing components to target cells or tissues.
  - 근거: corpus: definition, corpus: technique
- **C4.** The invention must be applicable to a wide range of organisms, including plants, animals, and microorganisms.
  - 근거: corpus: definition, corpus: task
- **C5.** The invention must involve the use of nucleases, such as CRISPR-Cas9, or other genome editing enzymes to achieve targeted genetic modifications.
  - 근거: corpus: technique, corpus: signal_term
- **C6.** The invention must demonstrate specificity in targeting and minimizing off-target effects in genome editing.
  - 근거: corpus: technique, corpus: task

## 분석 대상 특허의 범위
The scope of analysis for genome editing technology includes patents that implement, improve, or provide enabling components or methods specific to genome editing. This encompasses inventions that perform precise DNA alterations, deliver editing components, or apply genome editing to specific organisms or applications. Patents that merely use genome editing outputs or vocabulary for unrelated purposes are excluded.

## 범위 결정 (클러스터별 in/out)

- [IN] **CRISPR-Cas9 technology** — CRISPR-Cas9 technology is a core genome editing technique that enables precise DNA alterations, fitting the domain's defining tasks.
- [IN] **gene editing methods** — Gene editing methods that involve precise DNA sequence alterations are central to the domain of genome editing technology.
- [IN] **homologous recombination** — Homologous recombination is a method used in genome editing to introduce specific genetic changes, aligning with the domain's purpose.
- [CONDITIONAL] **plant genetic engineering** — Plant genetic engineering is in scope if it involves direct genome editing techniques; otherwise, it is out if it only involves traditional genetic modification without precise editing.
- [CONDITIONAL] **gene therapy applications** — Gene therapy applications are in scope if they involve direct genome editing techniques; otherwise, they are out if they only involve therapeutic uses of nucleic acids without editing.
- [IN] **RNA-guided endonucleases** — RNA-guided endonucleases, such as those used in CRISPR systems, are essential tools for precise genome editing.
- [IN] **gene knockout techniques** — Gene knockout techniques that involve precise genome editing are within the domain as they perform a defining task.
- [CONDITIONAL] **transgenic organism development** — Transgenic organism development is in scope if it involves genome editing techniques; otherwise, it is out if it involves traditional genetic engineering without precise editing.
- [CONDITIONAL] **nucleic acid therapeutics** — Nucleic acid therapeutics are in scope if they involve genome editing techniques; otherwise, they are out if they only involve therapeutic uses without editing.
- [CONDITIONAL] **high-throughput gene screening** — High-throughput gene screening is in scope if it directly involves genome editing techniques; otherwise, it is out if it does not involve genome editing.

## 제외 기준 (E)

- **E1.** Patents that focus on gene expression modulation without direct genome editing techniques are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E2.** Patents involving genetic modification in specific organisms without broader genome editing context are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E3.** Patents related to recombinant virus construction for therapeutic purposes rather than direct genome editing are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E4.** Patents discussing high-throughput screening methods without direct genome editing are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E5.** Patents involving plant biotechnology applications without explicit genome editing techniques are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E6.** Patents focusing on diagnostic methods using CRISPR without editing are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E7.** Patents related to therapeutic applications using nucleic acids without direct genome editing are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E8.** Patents involving genetic engineering for vaccine development rather than genome editing are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E9.** Patents discussing SNP markers and genetic analysis without direct editing are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E10.** Patents focusing on bioprinting or material production without genome editing are excluded.
  - 근거: corpus: suspected_boundary_cases

## 경계 판정 지침

- For patents focusing on gene expression modulation without direct genome editing techniques, such as 'Modulation of jerky-like 1 expression', exclude them as they do not perform genome editing tasks.
- For patents involving genetic modification in specific organisms without broader genome editing context, like 'A kind of infectious spleen and kidney necrosis virus ORF069 gene-deleted strains and its preparation method and application', exclude them unless they involve precise genome editing techniques.
- For patents related to recombinant virus construction for therapeutic purposes rather than direct genome editing, such as 'Use and constructing method for anticancer recombined gland virus with tumour cell PLK1 as target of medicine', exclude them as they do not involve genome editing.
- For patents discussing high-throughput screening methods without direct genome editing, like 'Method for high-throughput screening of essential genes and growth inhibitory genes of eukaryotes', exclude them unless they directly involve genome editing techniques.
- For patents involving plant biotechnology applications without explicit genome editing techniques, such as 'Application of GT1 gene in regulation and control of maize male inflorescence sex determination and/or multi-spike development', exclude them unless they involve genome editing.
- For patents focusing on diagnostic methods using CRISPR without editing, like 'Method for detecting the antibiotic resistance gene blavim-2', exclude them as they do not involve genome editing.
- For patents related to therapeutic applications using nucleic acids without direct genome editing, such as 'Nucleic acid-based therapeutics', exclude them unless they involve genome editing.
- For patents involving genetic engineering for vaccine development rather than genome editing, like 'Duck circovirus genetic engineering subunit vaccine and its preparation method and application', exclude them as they do not involve genome editing.
- For patents discussing SNP markers and genetic analysis without direct editing, such as 'Application of single-nucleotide-polymorphism rs55882956 in screening of Hansen's disease sufferers', exclude them as they do not involve genome editing.
- For patents focusing on bioprinting or material production without genome editing, like 'Bioprinter devices, systems and methods for printing soft gels for the treatment of musculoskeletal and skin disorders', exclude them as they do not involve genome editing.
