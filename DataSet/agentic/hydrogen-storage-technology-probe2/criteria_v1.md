# 도메인 판단 기준서 — Hydrogen Storage Technology

## 도메인 정의
Hydrogen storage technology encompasses methods and systems specifically designed to store hydrogen in a stable and energy-efficient manner, allowing for its safe containment and controlled release when needed. This includes technologies that utilize physical, chemical, or hybrid approaches to maintain hydrogen in a dense form, minimize energy loss during storage and retrieval, and ensure scalability to accommodate varying quantities of hydrogen. The technology must also address safety concerns related to hydrogen's flammability and potential for leakage.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the storage of hydrogen in a stable form, either through physical compression, liquefaction, or chemical bonding.
  - 근거: https://en.wikipedia.org/wiki/Hydrogen_storage, https://www.energy.gov/eere/fuelcells/hydrogen-storage
- **C2.** The invention must allow for the safe release of hydrogen when needed, ensuring controlled and efficient retrieval of stored hydrogen.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919319335
- **C3.** The invention must minimize energy loss during the storage and retrieval process, optimizing energy efficiency in hydrogen storage systems.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919319335
- **C4.** The invention must ensure the containment of hydrogen to prevent leaks, addressing safety concerns associated with hydrogen's flammability.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919319335
- **C5.** The invention must be scalable to accommodate varying quantities of hydrogen, allowing for flexibility in storage capacity.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919319335

## 분석 대상 특허의 범위
The scope of analysis for hydrogen storage technology includes patents that specifically address the storage, containment, and controlled release of hydrogen. This encompasses physical, chemical, and hybrid storage methods, as well as materials and systems designed to enhance the efficiency, safety, and scalability of hydrogen storage. Patents that focus on hydrogen production, conversion, or unrelated applications are outside the scope unless they directly contribute to or improve hydrogen storage capabilities.

## 범위 결정 (클러스터별 in/out)

- [IN] **Hydrogen storage alloys** — These alloys are specifically designed to store hydrogen, improving energy density and efficiency.
- [OUT] **Hydrogen generation systems** — These systems focus on producing hydrogen, not storing it.
- [OUT] **Hydrogen fuel cells** — Fuel cells use hydrogen for energy conversion, not storage.
- [IN] **Hydrogen storage materials** — These materials are specifically developed to store hydrogen efficiently and safely.
- [CONDITIONAL] **Hydrogen recovery systems** — In if the system is specifically designed to recover hydrogen for storage purposes; out if it focuses on recovery for immediate use or conversion.
- [OUT] **Hydrogen production methods** — These methods focus on producing hydrogen, not storing it.
- [CONDITIONAL] **Hydrogen separation technologies** — In if the separation is specifically for storage purposes; out if it is for purification or other uses.

## 제외 기준 (E)

- **E1.** Patents that focus on hydrogen production or conversion without addressing storage are excluded.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage
- **E2.** Patents that use hydrogen in unrelated applications, such as semiconductor manufacturing or plastic decomposition, are excluded unless they specifically enhance hydrogen storage capabilities.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage

## 경계 판정 지침

- Cooling tower patents are out as they focus on cooling technology, not hydrogen storage.
- Electrochemical reaction apparatus patents are out unless they specifically address hydrogen storage.
- Gasification of plastics patents are out as they focus on plastic decomposition, not hydrogen storage.
- Low alloy steel patents are out unless they specifically enhance hydrogen storage capabilities in high-pressure environments.

## 사용자 결정이 필요한 범위 질문

- **Q1. Should hydrail applications be included in the hydrogen storage domain?**
  - 영향: Hydrail applications involve hydrogen storage for transportation, which could be considered a specific application of storage technology.
  - 선택지: Include hydrail applications as they involve hydrogen storage for transportation., Exclude hydrail applications as they primarily focus on transportation rather than storage.
  - 현재 가정(미답변 시): Exclude hydrail applications as they primarily focus on transportation rather than storage.
