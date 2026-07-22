# 특허 도메인 판단 기준서 — Hydrogen Storage Technology

## 도메인 정의

Hydrogen Storage Technology encompasses inventions that enable the storage of hydrogen in a stable and efficient manner, allowing for its safe containment and subsequent release when needed. This includes methods and systems that optimize the volume and weight efficiency of storage, ensure compatibility with existing hydrogen production and utilization systems, and employ advanced materials or techniques specific to hydrogen storage. The domain covers both mechanical and chemical storage methods, as well as innovations that enhance the safety, stability, and efficiency of hydrogen storage processes.

## 기술축

### A1. Hydrogen Storage Methods [core/high]

Methods for storing hydrogen, including mechanical approaches like high pressures and low temperatures, and chemical compounds that release H2 on demand.

- 사용자 문서 명시: False
특허 풀 관찰: True
판단 근거: Supported by both web evidence and corpus clusters, indicating a core aspect of the domain.
- 출처:
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Hydrogen storage methods include mechanical approaches like high pressures and low temperatures, and chemical compounds that release H2 on demand.
  - [corpus/high] corpus:cluster:1: Hydrogen storage alloys are a main cluster in the patent pool.

### A2. Safety and Stability of Hydrogen Storage [core/high]

Ensuring the safety and stability of hydrogen storage under various conditions, including pressure and temperature management.

- 사용자 문서 명시: False
특허 풀 관찰: True
판단 근거: Safety is a critical aspect of hydrogen storage, supported by user query, web evidence, and corpus clusters.
- 출처:
  - [user_query/high] query.json: The technology must ensure the safety of hydrogen storage under various conditions.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Compressed hydrogen storage involves keeping hydrogen gas under pressure to increase storage density.
  - [corpus/high] corpus:cluster:4: Materials for high-pressure hydrogen environments are a main cluster in the patent pool.

### A3. Efficiency of Hydrogen Release [core/high]

Technologies that allow for the efficient release of hydrogen when needed, including electrochemical and thermal methods.

- 사용자 문서 명시: False
특허 풀 관찰: True
판단 근거: Efficiency in hydrogen release is essential for practical applications, supported by user query, web evidence, and corpus cases.
- 출처:
  - [user_query/high] query.json: The technology must allow for the efficient release of hydrogen when needed.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Electrochemical hydrogen storage allows controlled release of hydrogen using electricity.
  - [corpus/high] corpus:case:1: Hydrogen storage alloys for improved efficiency.

### A4. Volume and Weight Efficiency [core/high]

Optimizing the volume and weight efficiency of hydrogen storage systems to enhance portability and usability.

- 사용자 문서 명시: False
특허 풀 관찰: True
판단 근거: Volume and weight efficiency is crucial for mobile applications, supported by user query and web evidence, though underrepresented in the corpus.
- 출처:
  - [user_query/high] query.json: The technology must optimize the volume and weight efficiency of hydrogen storage.
  - [web/high] https://en.wikipedia.org/wiki/Liquid_hydrogen: Storing hydrogen as a liquid takes less space than storing it as a gas at normal temperature and pressure.
  - [corpus/high] corpus:mismatch:2: The pool does not prominently feature liquid hydrogen storage, despite its significance in web evidence.

### A5. Compatibility with Hydrogen Systems [core/medium]

Ensuring compatibility of hydrogen storage technologies with existing hydrogen production and utilization systems.

- 사용자 문서 명시: False
특허 풀 관찰: True
판단 근거: Compatibility is necessary for integration into existing systems, supported by user query, web evidence, and corpus cases.
- 출처:
  - [user_query/high] query.json: The technology must be compatible with existing hydrogen production and utilization systems.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_technologies: Hydrogen technologies can be carbon neutral and contribute to preventing climate change.
  - [corpus/high] corpus:case:2: Advanced hydrogen generation systems for industrial applications.

### A6. Advanced Materials for Hydrogen Storage [supplemental/medium]

Use of advanced materials such as metal-organic frameworks (MOFs) and nanomaterials to enhance hydrogen storage capabilities.

- 사용자 문서 명시: False
특허 풀 관찰: False
판단 근거: Advanced materials are highlighted in web evidence but are underrepresented in the patent pool, suggesting a supplemental role.
- 출처:
  - [web/high] https://en.wikipedia.org/wiki/Metal–organic_framework: Metal–organic frameworks (MOFs) are used for hydrogen storage due to their porous nature.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Nanomaterials can enhance hydrogen storage by improving sorption kinetics and storage capacity.
  - [corpus/high] corpus:mismatch:1: The patent pool lacks emphasis on Metal–Organic Frameworks (MOFs) for hydrogen storage, which are highlighted in web evidence.

## 포함 판단 기준 (C)

- **C1.** The invention must provide a method or system for storing hydrogen, including mechanical approaches like high pressures and low temperatures, or chemical compounds that release hydrogen on demand.
  - 관찰 신호(비배타적 단서): hydrogen storage, high pressure, low temperature, chemical compound, release hydrogen
  - 기술축: A1
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Hydrogen storage methods include mechanical approaches like high pressures and low temperatures, and chemical compounds that release H2 on demand.
  - [corpus/high] corpus:cluster:1: Hydrogen storage alloys are a main cluster in the patent pool.
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, corpus:cluster:1
- **C2.** The invention must ensure the safety and stability of hydrogen storage under various conditions, including pressure and temperature management.
  - 관찰 신호(비배타적 단서): safety, stability, pressure management, temperature management, hydrogen storage
  - 기술축: A2
  - [user_query/high] query.json: The technology must ensure the safety of hydrogen storage under various conditions.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Compressed hydrogen storage involves keeping hydrogen gas under pressure to increase storage density.
  - [corpus/high] corpus:cluster:4: Materials for high-pressure hydrogen environments are a main cluster in the patent pool.
  - 레거시 출처: query.json, https://en.wikipedia.org/wiki/Hydrogen_storage, corpus:cluster:4
- **C3.** The invention must allow for the efficient release of hydrogen when needed, including electrochemical and thermal methods.
  - 관찰 신호(비배타적 단서): efficient release, electrochemical, thermal method, hydrogen release, controlled release
  - 기술축: A3
  - [user_query/high] query.json: The technology must allow for the efficient release of hydrogen when needed.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Electrochemical hydrogen storage allows controlled release of hydrogen using electricity.
  - [corpus/high] corpus:case:1: Hydrogen storage alloys for improved efficiency.
  - 레거시 출처: query.json, https://en.wikipedia.org/wiki/Hydrogen_storage, corpus:case:1
- **C4.** The invention must optimize the volume and weight efficiency of hydrogen storage systems to enhance portability and usability.
  - 관찰 신호(비배타적 단서): volume efficiency, weight efficiency, portability, usability, liquid hydrogen
  - 기술축: A4
  - [user_query/high] query.json: The technology must optimize the volume and weight efficiency of hydrogen storage.
  - [web/high] https://en.wikipedia.org/wiki/Liquid_hydrogen: Storing hydrogen as a liquid takes less space than storing it as a gas at normal temperature and pressure.
  - [corpus/high] corpus:mismatch:2: The pool does not prominently feature liquid hydrogen storage, despite its significance in web evidence.
  - 레거시 출처: query.json, https://en.wikipedia.org/wiki/Liquid_hydrogen, corpus:mismatch:2
- **C5.** The invention must ensure compatibility of hydrogen storage technologies with existing hydrogen production and utilization systems.
  - 관찰 신호(비배타적 단서): compatibility, hydrogen production, utilization systems, integration, existing systems
  - 기술축: A5
  - [user_query/high] query.json: The technology must be compatible with existing hydrogen production and utilization systems.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_technologies: Hydrogen technologies can be carbon neutral and contribute to preventing climate change.
  - [corpus/high] corpus:case:2: Advanced hydrogen generation systems for industrial applications.
  - 레거시 출처: query.json, https://en.wikipedia.org/wiki/Hydrogen_technologies, corpus:case:2

## 분석 대상 특허의 범위

The scope of analysis for Hydrogen Storage Technology includes patents that implement, improve, or provide enabling components or methods specific to the storage of hydrogen. This encompasses mechanical and chemical storage methods, safety and stability enhancements, efficiency improvements in hydrogen release, and compatibility with existing hydrogen systems. Patents that merely use hydrogen storage outputs or vocabulary for unrelated purposes are excluded.

## 범위 결정

- [IN] **Hydrogen storage alloys** — These patents directly relate to methods and materials for storing hydrogen, a core aspect of the domain.
- [OUT] **Hydrogen generation systems** — While related to hydrogen, these systems focus on production rather than storage, which is outside the domain's core task.
- [OUT] **Hydrogen fuel cells** — Fuel cells focus on the utilization of hydrogen rather than its storage, thus falling outside the domain.
- [IN] **High-pressure hydrogen environments** — These patents address safety and stability in hydrogen storage, aligning with core domain tasks.
- [OUT] **Hydrogen recovery systems** — These systems focus on recovering hydrogen from processes, not on its storage, thus outside the domain.
- [OUT] **Cooling tower** — This technology focuses on cooling, not directly related to hydrogen storage.
- [CONDITIONAL] **Electrochemical reaction apparatus** — In if the apparatus specifically addresses hydrogen storage; out if it involves general electrochemical processes.
- [OUT] **Process for preparing aromatic polyamides** — This process relates to chemical manufacturing, not hydrogen storage.
- [OUT] **Gasification of plastics** — Focuses on hydrogen generation, not storage.
- [OUT] **Low-temperature plasma device** — Involves hydrogen sulfide decomposition, not hydrogen storage.
- [OUT] **Home fuel cell boiler system** — Relates to fuel cells, not specifically to hydrogen storage.

## 제외 판단 기준 (E)

- **E1.** Patents that focus on hydrogen generation rather than storage are excluded from the domain.
  - 관찰 신호(비배타적 단서): hydrogen generation, gasification, production, synthesis, generation system
  - [corpus/high] corpus:boundary:4: Gasification of plastics — discusses hydrogen generation but not storage.
  - 레거시 출처: corpus:boundary:4
- **E2.** Patents that focus on the utilization of hydrogen, such as fuel cells, rather than its storage, are excluded from the domain.
  - 관찰 신호(비배타적 단서): fuel cell, utilization, combustion, energy conversion, power generation
  - [corpus/high] corpus:boundary:6: Home fuel cell boiler system having combustion catalysis device — relates to fuel cells but not specifically to hydrogen storage.
  - 레거시 출처: corpus:boundary:6

## 경계 판정 지침

- Electrochemical reaction apparatus is in if it specifically addresses hydrogen storage; out if it involves general electrochemical processes.

## HITL이 필요한 범위 질문

- **Q1. Should the domain include electrochemical reaction apparatuses that do not specifically address hydrogen storage?**
  - 영향: Electrochemical processes can be used for both storage and other purposes, affecting domain inclusion.
  - 선택지: Include all electrochemical apparatuses related to hydrogen., Include only those specifically addressing hydrogen storage.
  - 미응답 기본값: Include only those specifically addressing hydrogen storage.
