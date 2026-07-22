# 특허 도메인 판단 기준서 — Hydrogen Storage Technology

## 도메인 정의

Hydrogen Storage Technology encompasses inventions that enable the storage of hydrogen in a stable and safe form, allowing for its efficient release and transfer when needed. This includes methods and materials that maximize storage density, ensure safety under various environmental conditions, and facilitate the efficient transfer of hydrogen into and out of storage systems. The technology is specific to storing hydrogen, not its production or utilization, and involves mechanical, chemical, and advanced material approaches.

## 기술축

### A1. Hydrogen Storage Methods [core/high]

Technologies and methods used to store hydrogen, including mechanical, chemical, and advanced material approaches.

- 사용자 문서 명시: False
특허 풀 관찰: True
판단 근거: The core of hydrogen storage technology involves various methods to store hydrogen safely and efficiently, as supported by both web evidence and corpus cases.
- 출처:
  - [user_query/high] query.json: The technology must enable the storage of hydrogen in a stable form.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Hydrogen storage methods include mechanical approaches like high pressures and low temperatures, and chemical compounds that release H2 on demand.
  - [corpus/high] corpus:case:1: Hydrogen storage alloys

### A2. Safety and Stability [core/high]

Ensuring the safe storage and release of hydrogen under various environmental conditions.

- 사용자 문서 명시: False
특허 풀 관찰: False
판단 근거: Safety is a critical aspect of hydrogen storage, ensuring that hydrogen can be stored and released without risk, supported by user query and web evidence.
- 출처:
  - [user_query/high] query.json: The technology must ensure the safety of hydrogen storage under various environmental conditions.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: The release temperature of hydrogen storage materials affects the cost and efficiency of storage strategies.

### A3. Storage Density Optimization [core/high]

Maximizing the storage density of hydrogen to optimize space and weight.

- 사용자 문서 명시: False
특허 풀 관찰: True
판단 근거: Optimizing storage density is essential for practical applications, supported by both user query and corpus evidence.
- 출처:
  - [user_query/high] query.json: The technology should maximize the storage density of hydrogen to optimize space and weight.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Compressed hydrogen storage involves keeping hydrogen gas under pressure to increase storage density.
  - [corpus/high] corpus:case:4: Hydrogen storage materials

### A4. Efficient Hydrogen Transfer [core/high]

Facilitating the efficient transfer of hydrogen into and out of the storage system.

- 사용자 문서 명시: False
특허 풀 관찰: False
판단 근거: Efficient transfer mechanisms are crucial for the usability of hydrogen storage systems, supported by user query and web evidence.
- 출처:
  - [user_query/high] query.json: The technology should facilitate the efficient transfer of hydrogen into and out of the storage system.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Electrochemical hydrogen storage allows controlled release of hydrogen using electricity.

### A5. Advanced Materials for Hydrogen Storage [supplemental/medium]

Use of advanced materials like metal-organic frameworks (MOFs) and nanomaterials to enhance hydrogen storage capabilities.

- 사용자 문서 명시: False
특허 풀 관찰: False
판단 근거: While not emphasized in the corpus, advanced materials like MOFs are significant in web evidence for enhancing hydrogen storage.
- 출처:
  - [web/high] https://en.wikipedia.org/wiki/Metal–organic_framework: Metal–organic frameworks (MOFs) are used for hydrogen storage due to their porous nature.
  - [corpus/high] corpus:mismatch:1: The patent pool does not emphasize Metal–Organic Frameworks (MOFs) for hydrogen storage, which are highlighted in web evidence as significant.

## 포함 판단 기준 (C)

- **C1.** The invention must enable the storage of hydrogen in a stable form, using mechanical, chemical, or advanced material methods.
  - 관찰 신호(비배타적 단서): hydrogen storage, mechanical storage, chemical storage, advanced materials, metal hydrides
  - 기술축: A1
  - [user_query/high] query.json: The technology must enable the storage of hydrogen in a stable form.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Hydrogen storage methods include mechanical approaches like high pressures and low temperatures, and chemical compounds that release H2 on demand.
  - [corpus/high] corpus:case:1: Hydrogen storage alloys
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, query.json, corpus:case:1
- **C2.** The invention must allow for the safe release of hydrogen when needed, ensuring safety under various environmental conditions.
  - 관찰 신호(비배타적 단서): safe release, environmental conditions, pressure containment, release temperature, safety mechanisms
  - 기술축: A2
  - [user_query/high] query.json: The technology must ensure the safety of hydrogen storage under various environmental conditions.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: The release temperature of hydrogen storage materials affects the cost and efficiency of storage strategies.
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, query.json
- **C3.** The invention should maximize the storage density of hydrogen to optimize space and weight.
  - 관찰 신호(비배타적 단서): storage density, compressed hydrogen, space optimization, weight optimization, nanomaterials
  - 기술축: A3
  - [user_query/high] query.json: The technology should maximize the storage density of hydrogen to optimize space and weight.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Compressed hydrogen storage involves keeping hydrogen gas under pressure to increase storage density.
  - [corpus/high] corpus:case:4: Hydrogen storage materials
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, query.json, corpus:case:4
- **C4.** The invention must facilitate the efficient transfer of hydrogen into and out of the storage system.
  - 관찰 신호(비배타적 단서): hydrogen transfer, efficient transfer, refueling systems, electrochemical storage, controlled release
  - 기술축: A4
  - [user_query/high] query.json: The technology should facilitate the efficient transfer of hydrogen into and out of the storage system.
  - [web/high] https://en.wikipedia.org/wiki/Hydrogen_storage: Electrochemical hydrogen storage allows controlled release of hydrogen using electricity.
  - 레거시 출처: https://en.wikipedia.org/wiki/Hydrogen_storage, query.json
- **C5.** The invention may involve the use of advanced materials like metal-organic frameworks (MOFs) to enhance hydrogen storage capabilities.
  - 관찰 신호(비배타적 단서): MOFs, metal-organic frameworks, advanced materials, porous structures, sorption kinetics
  - 기술축: A5
  - [web/high] https://en.wikipedia.org/wiki/Metal–organic_framework: Metal–organic frameworks (MOFs) are used for hydrogen storage due to their porous nature.
  - [corpus/high] corpus:mismatch:1: The patent pool does not emphasize Metal–Organic Frameworks (MOFs) for hydrogen storage, which are highlighted in web evidence as significant.
  - 레거시 출처: https://en.wikipedia.org/wiki/Metal–organic_framework, corpus:mismatch:1

## 분석 대상 특허의 범위

The scope of analysis for Hydrogen Storage Technology includes patents that specifically address the storage of hydrogen, focusing on methods and materials that enable stable, safe, and efficient storage and release of hydrogen. This includes mechanical, chemical, and advanced material approaches, as well as systems that optimize storage density and facilitate hydrogen transfer. Patents related to hydrogen production, utilization, or unrelated technologies are excluded.

## 범위 결정

- [IN] **Hydrogen storage alloys** — These patents focus on materials specifically designed for storing hydrogen, which is a core aspect of the domain.
- [OUT] **Hydrogen generation systems** — These patents focus on the production of hydrogen, not its storage, which is outside the domain's scope.
- [OUT] **Hydrogen fuel cells** — Fuel cells are primarily concerned with the utilization of hydrogen, not its storage.
- [IN] **Hydrogen storage materials** — These patents focus on materials specifically designed for storing hydrogen, which is a core aspect of the domain.
- [CONDITIONAL] **Hydrogen recovery systems** — In if the system specifically addresses the recovery of hydrogen for storage purposes; out if it focuses on recovery for immediate use or other processes.
- [OUT] **Hydrogen production methods** — These patents focus on the production of hydrogen, not its storage, which is outside the domain's scope.
- [CONDITIONAL] **Hydrogen separation technologies** — In if the separation technology is specifically designed to enhance hydrogen storage; out if it is for general separation purposes.

## 제외 판단 기준 (E)

- **E1.** Patents that focus on hydrogen production methods rather than storage are excluded.
  - 관찰 신호(비배타적 단서): hydrogen production, generation systems, gasification, production methods
  - 기술축: A1
  - [corpus/high] corpus:boundary:3: This patent discusses hydrogen generation from plastics but does not focus on storage technology.
  - 레거시 출처: corpus:boundary:3
- **E2.** Patents that involve hydrogen utilization, such as fuel cells, without addressing storage are excluded.
  - 관찰 신호(비배타적 단서): fuel cells, hydrogen utilization, combustion catalysis, energy conversion
  - 기술축: A1
  - [corpus/high] corpus:boundary:5: This patent involves fuel cells but does not specifically address hydrogen storage.
  - 레거시 출처: corpus:boundary:5
- **E3.** Patents that mention hydrogen but focus on unrelated technologies, such as semiconductor processes, are excluded.
  - 관찰 신호(비배타적 단서): semiconductor, unrelated technology, processes, manufacturing
  - 기술축: A1
  - [corpus/high] corpus:boundary:6: While it mentions hydrogen, it focuses on semiconductor processes rather than hydrogen storage or production.
  - 레거시 출처: corpus:boundary:6

## 경계 판정 지침

- For patents related to hydrogen recovery systems, determine if the recovery is specifically for storage purposes to decide inclusion.
- For hydrogen separation technologies, assess if the separation is designed to enhance storage capabilities to decide inclusion.

## HITL이 필요한 범위 질문

- **Q1. Should hydrogen recovery systems be included if they focus on recovery for storage purposes?**
  - 영향: This decision affects whether patents that recover hydrogen specifically for storage are included, impacting the domain's breadth.
  - 선택지: Include only if recovery is for storage purposes., Exclude all recovery systems regardless of purpose.
  - 미응답 기본값: Include only if recovery is for storage purposes.
- **Q2. Should hydrogen separation technologies be included if they are designed to enhance storage capabilities?**
  - 영향: This decision affects whether separation technologies that specifically enhance storage are included, impacting the domain's breadth.
  - 선택지: Include if designed to enhance storage capabilities., Exclude all separation technologies regardless of design.
  - 미응답 기본값: Include if designed to enhance storage capabilities.
