# 특허 도메인 판단 기준서 — Hydrogen Storage Technology

## 도메인 정의

Hydrogen Storage Technology encompasses inventions that enable the storage of hydrogen in a stable and efficient manner, allowing for its safe containment and subsequent release when needed. This includes methods and materials specifically designed to store hydrogen, optimize storage capacity, and ensure compatibility with existing hydrogen production and utilization systems. The technology must address the challenges of volume and weight optimization, safety under various conditions, and efficient hydrogen release, while being applicable to both stationary and mobile applications.

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

- **C1.** The invention must involve a method or material specifically designed for storing hydrogen in a stable form.
  - 관찰 신호(비배타적 단서): hydrogen storage, mechanical storage, chemical storage, nanomaterials, metal hydrides
  - 기술축: A1
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Hydrogen storage methods include mechanical approaches like high pressures and low temperatures, and chemical compounds that release H2 on demand.
  - [corpus/high] corpus: hydrogen storage materials: Hydrogen storage materials and methods for enhancing storage capacity
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, corpus:case:1
- **C2.** The invention must enable the efficient release of stored hydrogen when needed.
  - 관찰 신호(비배타적 단서): hydrogen release, controlled release, temperature control, release efficiency
  - 기술축: A2
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: The release temperature of hydrogen storage materials affects the cost of chemical storage strategies.
  - [user_query/high] query.json: The technology must allow for the efficient release of hydrogen when needed.
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, query.json
- **C3.** The invention must ensure the safety of hydrogen storage under various conditions, including pressure and temperature extremes.
  - 관찰 신호(비배타적 단서): safety mechanisms, pressure control, temperature control, safety standards
  - 기술축: A3
  - [user_query/high] query.json: The technology must ensure the safety of hydrogen storage under various conditions.
  - 레거시 출처: query.json
- **C4.** The invention must optimize the volume and weight of hydrogen storage systems to enhance energy density and portability.
  - 관찰 신호(비배타적 단서): volume optimization, weight reduction, energy density, portable storage
  - 기술축: A4
  - [user_query/high] query.json: The technology must optimize the volume and weight of hydrogen storage systems.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Hydrogen storage in vehicles requires storing hydrogen in an energy-dense form to provide sufficient driving range.
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, query.json
- **C5.** The invention must be compatible with existing hydrogen production and utilization systems.
  - 관찰 신호(비배타적 단서): system compatibility, integration with fuel cells, hydrogen production, utilization systems
  - 기술축: A5
  - [user_query/high] query.json: The technology must be compatible with existing hydrogen production and utilization systems.
  - [corpus/high] corpus: hydrogen production methods: Innovative hydrogen production methods using renewable energy sources
  - 레거시 출처: query.json, corpus:case:3
- **C6.** The invention must involve the use of Metal-Organic Frameworks (MOFs) for hydrogen storage, leveraging their high surface area and porosity.
  - 관찰 신호(비배타적 단서): MOFs, high surface area, porosity, hydrogen uptake
  - 기술축: A7
  - [web/high] https://en.wikipedia.org/wiki/Metal–organic_framework: Metal–organic frameworks (MOFs) are used for hydrogen storage due to their porous nature.
  - [corpus/high] corpus:mismatch:1: The patent pool lacks emphasis on metal-organic frameworks (MOFs) for hydrogen storage, which are highlighted in web evidence as significant.
  - 레거시 출처: https://en.wikipedia.org/wiki/Metal–organic_framework, corpus:mismatch:1
- **C7.** The invention must involve the use of nanomaterials to enhance hydrogen storage capacity and kinetics.
  - 관찰 신호(비배타적 단서): nanomaterials, sorption kinetics, storage capacity, carbon nanotubes
  - 기술축: A6
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Nanomaterials can enhance hydrogen storage by improving sorption kinetics and storage capacity.
  - [corpus/high] corpus:mismatch:3: The pool does not reflect the web's emphasis on nanomaterials for enhancing hydrogen storage, which is a key technique mentioned online.
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, corpus:mismatch:3

## 분석 대상 특허의 범위

The scope of analysis for Hydrogen Storage Technology includes patents that specifically address the storage, release, and safety of hydrogen as a fuel. This encompasses methods and materials designed for hydrogen storage, including mechanical, chemical, and nanomaterial-based approaches, as well as technologies that ensure compatibility with existing hydrogen systems. Patents that focus on the handling or production of hydrogen without a specific storage component are excluded.

## 범위 결정

- [OUT] **hydrogen production methods** — While related to hydrogen technology, production methods do not specifically address the storage of hydrogen, which is the core focus of this domain.
- [IN] **hydrogen storage materials** — These patents directly involve materials and methods for storing hydrogen, aligning with the core purpose of the domain.
- [OUT] **hydrogen purification techniques** — Purification techniques focus on refining hydrogen rather than storing it, thus falling outside the domain's scope.
- [OUT] **fuel cell systems** — Fuel cell systems utilize hydrogen but do not specifically address its storage, which is the domain's focus.
- [OUT] **hydrogen recovery systems** — Recovery systems focus on reclaiming hydrogen rather than storing it, which is outside the domain's scope.
- [OUT] **hydrogen generation systems** — Generation systems focus on producing hydrogen, not storing it, thus they are outside the domain's scope.
- [OUT] **Air supply systems for fuel cells** — These systems focus on air management rather than hydrogen storage, which is the domain's focus.
- [CONDITIONAL] **Liquid hydrogen handling technologies** — Liquid hydrogen handling technologies are included if they directly contribute to the storage solution, particularly in terms of safety and efficiency.

## 제외 판단 기준 (E)

- **E1.** Patents that focus solely on hydrogen production methods without addressing storage are excluded.
  - 관찰 신호(비배타적 단서): hydrogen production, electrolysis, renewable hydrogen
  - [corpus/high] corpus:cluster:1: hydrogen production methods
  - 레거시 출처: corpus:cluster:1
- **E2.** Patents that focus on hydrogen purification techniques without a storage component are excluded.
  - 관찰 신호(비배타적 단서): purification, refining, hydrogen purity
  - [corpus/high] corpus:cluster:3: hydrogen purification techniques
  - 레거시 출처: corpus:cluster:3
- **E3.** Patents that focus on fuel cell systems without addressing hydrogen storage are excluded.
  - 관찰 신호(비배타적 단서): fuel cell, electricity generation, hydrogen utilization
  - [corpus/high] corpus:cluster:4: fuel cell systems
  - 레거시 출처: corpus:cluster:4

## 경계 판정 지침

- Air supply systems for fuel cells are out of scope as they focus on air management rather than hydrogen storage.
- Liquid hydrogen handling technologies are out of scope as they focus on handling rather than storage.

## HITL이 필요한 범위 질문

- **Q1. Should the domain include nanomaterials specifically for enhancing hydrogen storage capacity?**
  - 영향: 측정: 풀 표본 20건 중 2건(~10%)의 판정이 넓게/좁게에 따라 갈립니다. Nanomaterials are highlighted in web evidence as significant for hydrogen storage, but are underrepresented in the patent pool.
  - 선택지: Include nanomaterials for hydrogen storage, Exclude nanomaterials for hydrogen storage
  - 미응답 기본값: Include nanomaterials for hydrogen storage
