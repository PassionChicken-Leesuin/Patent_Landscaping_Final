# 특허 도메인 판단 기준서 — Hydrogen Storage Technology

## 도메인 정의

Hydrogen Storage Technology encompasses inventions that enable the storage of hydrogen in a stable and efficient manner, ensuring safe containment and release of hydrogen under various conditions. This includes methods and materials specifically designed for hydrogen storage, such as mechanical, chemical, and nanomaterial-based approaches, as well as technologies that optimize the volume and weight of storage systems and ensure compatibility with existing hydrogen production and utilization systems.

## 기술축

### A1. Hydrogen Storage Methods [core/high]

Methods for storing hydrogen, including mechanical, chemical, and nanomaterial-based approaches.

- 사용자 문서 명시: False
특허 풀 관찰: True
판단 근거: Both web and corpus evidence strongly support the inclusion of various hydrogen storage methods as a core axis.
- 출처:
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Hydrogen storage methods include mechanical approaches like high pressures and low temperatures, and chemical compounds that release H2 on demand.
  - [corpus/high] corpus: hydrogen storage materials: Hydrogen storage materials and methods for enhancing storage capacity

### A2. Hydrogen Release Efficiency [core/high]

Technologies that enable the efficient release of stored hydrogen when needed.

- 사용자 문서 명시: False
특허 풀 관찰: False
판단 근거: Efficient hydrogen release is critical for practical applications and is supported by both user query and web evidence.
- 출처:
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: The release temperature of hydrogen storage materials affects the cost of chemical storage strategies.
  - [user_query/high] query.json: The technology must allow for the efficient release of hydrogen when needed.

### A3. Safety of Hydrogen Storage [core/high]

Ensuring the safety of hydrogen storage under various conditions, including pressure and temperature extremes.

- 사용자 문서 명시: False
특허 풀 관찰: False
판단 근거: Safety is a fundamental requirement for hydrogen storage technologies, as highlighted in the user query.
- 출처:
  - [user_query/high] query.json: The technology must ensure the safety of hydrogen storage under various conditions.

### A4. Volume and Weight Optimization [core/high]

Optimizing the volume and weight of hydrogen storage systems to enhance energy density and portability.

- 사용자 문서 명시: False
특허 풀 관찰: False
판단 근거: Volume and weight optimization is crucial for mobile applications, supported by both user query and web evidence.
- 출처:
  - [user_query/high] query.json: The technology must optimize the volume and weight of hydrogen storage systems.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Hydrogen storage in vehicles requires storing hydrogen in an energy-dense form to provide sufficient driving range.

### A5. Compatibility with Hydrogen Systems [core/high]

Compatibility of hydrogen storage technologies with existing hydrogen production and utilization systems.

- 사용자 문서 명시: False
특허 풀 관찰: True
판단 근거: Compatibility with existing systems is essential for integration and scalability, supported by user query and corpus evidence.
- 출처:
  - [user_query/high] query.json: The technology must be compatible with existing hydrogen production and utilization systems.
  - [corpus/high] corpus: hydrogen production methods: Innovative hydrogen production methods using renewable energy sources

### A6. Nanomaterials for Hydrogen Storage [supplemental/medium]

Use of nanomaterials to enhance hydrogen storage capacity and kinetics.

- 사용자 문서 명시: False
특허 풀 관찰: False
판단 근거: Web evidence highlights the importance of nanomaterials, but this is not reflected in the corpus, suggesting a supplemental role.
- 출처:
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Nanomaterials can enhance hydrogen storage by improving sorption kinetics and storage capacity.
  - [corpus/high] corpus: The pool does not reflect the web's emphasis on nanomaterials for enhancing hydrogen storage, which is a key technique mentioned online.: The patent pool lacks emphasis on nanomaterials for hydrogen storage.

### A7. Metal-Organic Frameworks (MOFs) [supplemental/medium]

Application of MOFs in hydrogen storage due to their high surface area and porosity.

- 사용자 문서 명시: False
특허 풀 관찰: False
판단 근거: MOFs are significant in web evidence but underrepresented in the corpus, indicating a supplemental axis.
- 출처:
  - [web/high] https://en.wikipedia.org/wiki/Metal–organic_framework: Metal–organic frameworks (MOFs) are used for hydrogen storage due to their porous nature.
  - [corpus/high] corpus: The patent pool lacks emphasis on metal-organic frameworks (MOFs) for hydrogen storage, which are highlighted in web evidence as significant.: The patent pool lacks emphasis on MOFs for hydrogen storage.

## 포함 판단 기준 (C)

- **C1.** The invention must involve a method or material specifically designed for storing hydrogen, such as mechanical, chemical, or nanomaterial-based approaches.
  - 기술축: A1
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Hydrogen storage methods include mechanical approaches like high pressures and low temperatures, and chemical compounds that release H2 on demand.
  - [corpus/high] corpus: hydrogen storage materials: Hydrogen storage materials and methods for enhancing storage capacity
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, corpus: hydrogen storage materials
- **C2.** The invention must enable the efficient release of stored hydrogen when needed, such as through controlled temperature or pressure changes.
  - 기술축: A2
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: The release temperature of hydrogen storage materials affects the cost of chemical storage strategies.
  - [user_query/high] query.json: The technology must allow for the efficient release of hydrogen when needed.
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, query.json
- **C3.** The invention must ensure the safety of hydrogen storage under various conditions, including pressure and temperature extremes.
  - 기술축: A3
  - [user_query/high] query.json: The technology must ensure the safety of hydrogen storage under various conditions.
  - 레거시 출처: query.json
- **C4.** The invention must optimize the volume and weight of hydrogen storage systems to enhance energy density and portability.
  - 기술축: A4
  - [user_query/high] query.json: The technology must optimize the volume and weight of hydrogen storage systems.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Hydrogen storage in vehicles requires storing hydrogen in an energy-dense form to provide sufficient driving range.
  - 레거시 출처: query.json, https://en.wikipedia.org/wiki/Hydrogen_storage
- **C5.** The invention must be compatible with existing hydrogen production and utilization systems, facilitating integration and scalability.
  - 기술축: A5
  - [user_query/high] query.json: The technology must be compatible with existing hydrogen production and utilization systems.
  - [corpus/high] corpus: hydrogen production methods: Innovative hydrogen production methods using renewable energy sources
  - 레거시 출처: query.json, corpus: hydrogen production methods

## 분석 대상 특허의 범위

The scope of analysis for Hydrogen Storage Technology includes patents that implement, improve, or provide enabling components or methods specifically for hydrogen storage. This encompasses mechanical, chemical, and nanomaterial-based storage methods, as well as technologies that ensure safety, optimize volume and weight, and ensure compatibility with existing hydrogen systems. Patents that merely use hydrogen storage outputs for unrelated purposes or focus on handling rather than storage are excluded.

## 범위 결정

- [OUT] **hydrogen production methods** — While related to hydrogen technology, production methods do not specifically address the storage of hydrogen.
- [IN] **hydrogen storage materials** — These patents directly involve materials designed for storing hydrogen, aligning with the core domain tasks.
- [OUT] **hydrogen purification techniques** — Purification techniques focus on refining hydrogen rather than storing it.
- [OUT] **fuel cell systems** — Fuel cells utilize hydrogen but do not specifically address its storage.
- [OUT] **hydrogen recovery systems** — Recovery systems focus on reclaiming hydrogen rather than storing it.
- [OUT] **hydrogen generation systems** — Generation systems produce hydrogen but do not specifically address its storage.
- [OUT] **Air supply systems for fuel cells** — These systems focus on air management rather than hydrogen storage.
- [OUT] **Liquid hydrogen handling technologies** — Handling technologies relate to the management of liquid hydrogen rather than its storage.

## 제외 판단 기준 (E)

- **E1.** Patents that focus on hydrogen production methods without addressing storage are excluded.
  - 기술축: A5
  - [corpus/high] corpus: hydrogen production methods: Innovative hydrogen production methods using renewable energy sources
  - 레거시 출처: corpus: hydrogen production methods
- **E2.** Patents that focus on hydrogen purification techniques without addressing storage are excluded.
  - 기술축: A5
  - [corpus/high] corpus: hydrogen purification techniques: Advanced hydrogen purification techniques for fuel cell applications
  - 레거시 출처: corpus: hydrogen purification techniques
- **E3.** Patents that focus on fuel cell systems without addressing storage are excluded.
  - 기술축: A5
  - [corpus/high] corpus: fuel cell systems: fuel cell systems
  - 레거시 출처: corpus: fuel cell systems
- **E4.** Patents that focus on hydrogen recovery systems without addressing storage are excluded.
  - 기술축: A5
  - [corpus/high] corpus: hydrogen recovery systems: Hydrogen recovery systems for industrial applications
  - 레거시 출처: corpus: hydrogen recovery systems
- **E5.** Patents that focus on liquid hydrogen handling technologies without addressing storage are excluded.
  - 기술축: A5
  - [corpus/high] corpus: Liquid hydrogen handling technologies: Liquid hydrogen handling technologies, like 'Liquid hydrogen stand and liquid hydrogen automobile', relate to handling rather than the storage technology itself.
  - 레거시 출처: corpus: Liquid hydrogen handling technologies

## 경계 판정 지침

- Patents focusing on air supply systems for fuel cells are excluded as they do not address hydrogen storage.
- Patents related to liquid hydrogen handling are excluded unless they specifically address storage methods.

## HITL이 필요한 범위 질문

- **Q1. Should the domain include nanomaterials for hydrogen storage, despite their underrepresentation in the patent pool?**
  - 영향: Nanomaterials could significantly enhance hydrogen storage capacity and kinetics, impacting the domain's technological breadth.
  - 선택지: Include nanomaterials as a core part of the domain., Exclude nanomaterials due to their current underrepresentation.
  - 미응답 기본값: Include nanomaterials as a supplemental part of the domain.
- **Q2. Should the domain include metal-organic frameworks (MOFs) for hydrogen storage, given their significance in web evidence but lack of emphasis in the patent pool?**
  - 영향: MOFs are highlighted in web evidence as significant for hydrogen storage, potentially broadening the domain's scope.
  - 선택지: Include MOFs as a core part of the domain., Exclude MOFs due to their lack of emphasis in the patent pool.
  - 미응답 기본값: Include MOFs as a supplemental part of the domain.
