# 도메인 판단 기준서 — Hydrogen Storage Technology

## 도메인 정의
Hydrogen Storage Technology encompasses inventions that enable the storage of hydrogen in a stable and safe form, allowing for its controlled release when needed. This includes methods and materials that enhance storage density, minimize energy loss during storage and retrieval, and ensure containment to prevent leaks. The technology must be scalable to accommodate varying quantities of hydrogen and may involve mechanical, chemical, or electrochemical approaches specific to hydrogen storage.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the storage of hydrogen in a stable form, either through mechanical, chemical, or electrochemical means.
  - 근거: https://en.wikipedia.org/wiki/Hydrogen_storage, https://www.energy.gov/eere/fuelcells/hydrogen-storage
- **C2.** The invention must allow for the safe release of hydrogen when needed, ensuring controlled and efficient retrieval.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919319335
- **C3.** The invention must minimize energy loss during the storage and retrieval process of hydrogen.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919319335
- **C4.** The invention must ensure the containment of hydrogen to prevent leaks, addressing safety and environmental concerns.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919319335
- **C5.** The invention must be scalable to accommodate varying quantities of hydrogen, from small-scale applications to large industrial uses.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919319335
- **C6.** The invention must involve materials or methods specifically designed for hydrogen storage, such as metal hydrides, MOFs, or other advanced materials.
  - 근거: https://www.sciencedirect.com/science/article/pii/S0360319919319335, https://en.wikipedia.org/wiki/Metal%E2%80%93organic_framework

## 분석 대상 특허의 범위
The scope of analysis for Hydrogen Storage Technology includes patents that specifically address the storage of hydrogen, focusing on methods and materials that enable stable, safe, and efficient storage and retrieval. This encompasses mechanical, chemical, and electrochemical storage techniques, as well as innovations in materials specifically designed for hydrogen storage. Patents that merely use hydrogen for other purposes, such as production or conversion, are excluded unless they directly contribute to storage technology.

## 범위 결정 (클러스터별 in/out)

- [IN] **Hydrogen storage alloys** — These alloys are specifically designed for hydrogen storage, enabling stable and efficient storage and retrieval.
- [OUT] **Hydrogen generation systems** — These systems focus on producing hydrogen, not on storing it.
- [OUT] **Hydrogen fuel cells** — Fuel cells use hydrogen to generate electricity but do not focus on the storage of hydrogen.
- [IN] **Hydrogen storage materials** — These materials are specifically developed for storing hydrogen, aligning with the domain's core purpose.
- [CONDITIONAL] **Hydrogen recovery systems** — In if the system specifically involves recovering hydrogen for storage purposes; out if it focuses on recovery for immediate use or conversion.
- [OUT] **Hydrogen production methods** — These methods focus on producing hydrogen, not on storing it.
- [CONDITIONAL] **Hydrogen separation technologies** — In if the separation is specifically for storage purposes; out if it is for purification or other uses.

## 제외 기준 (E)

- **E1.** Patents that focus on hydrogen production or conversion without addressing storage are excluded.
  - 근거: corpus: Hydrogen generation systems, corpus: Hydrogen production methods
- **E2.** Patents that involve hydrogen use in applications like fuel cells or industrial processes without specific storage innovations are excluded.
  - 근거: corpus: Hydrogen fuel cells, corpus: Process for the treatment of crude oil using hydrogen
- **E3.** Patents that involve cooling or other processes not directly related to hydrogen storage are excluded.
  - 근거: corpus: Cooling tower, corpus: Semiconductor manufacturing apparatus

## 경계 판정 지침

- For 'Hydrogen recovery systems', include only if the recovery is specifically for storage purposes.
- For 'Hydrogen separation technologies', include only if the separation is specifically for storage purposes.

## 사용자 결정이 필요한 범위 질문

- **Q2. Should hydrogen separation technologies be included if they are not specifically for storage purposes?**
  - 영향: 측정: 풀 표본 60건 중 34건(~57%)의 판정이 넓게/좁게에 따라 갈립니다. This decision affects whether the domain covers broader separation technologies or focuses strictly on those aiding storage.
  - 선택지: Include all hydrogen separation technologies., Include only those specifically for storage purposes.
  - 현재 가정(미답변 시): Include only those specifically for storage purposes.
- **Q1. Does the domain include hydrogen recovery systems that are not specifically for storage purposes?**
  - 영향: 측정: 풀 표본 60건 중 33건(~55%)의 판정이 넓게/좁게에 따라 갈립니다. Including these systems could broaden the domain to cover more recovery technologies, while excluding them focuses strictly on storage.
  - 선택지: Include all hydrogen recovery systems., Include only those specifically for storage purposes.
  - 현재 가정(미답변 시): Include only those specifically for storage purposes.
