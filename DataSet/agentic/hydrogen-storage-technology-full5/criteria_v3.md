# 도메인 판단 기준서 — Hydrogen Storage Technology

## 도메인 정의
Hydrogen storage technology encompasses methods and systems designed to store hydrogen in a stable, efficient, and safe manner, allowing for its retrieval and use as an energy source. This includes technologies that enhance storage density, minimize energy loss during storage and retrieval, and ensure safety under various conditions. The domain covers mechanical, chemical, and material-based approaches specific to hydrogen storage, such as compressed gas, liquid hydrogen, metal hydrides, and advanced materials like metal-organic frameworks (MOFs).

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the storage of hydrogen in a stable form, such as through compression, liquefaction, or chemical bonding.
  - 근거: corpus: Hydrogen storage methods include mechanical approaches like high pressures and low temperatures, and chemical compounds that release H2 on demand.
- **C2.** The invention must facilitate the efficient retrieval of hydrogen for use, ensuring minimal energy loss during the process.
  - 근거: corpus: Electrochemical hydrogen storage allows controlled release of hydrogen using electricity.
- **C3.** The invention must incorporate safety measures to manage the risks associated with hydrogen's flammability and storage challenges.
  - 근거: corpus: Hydrogen safety involves managing the risks associated with hydrogen's flammability and storage challenges.
- **C4.** The invention must optimize the volume and weight efficiency of hydrogen storage, such as through the use of advanced materials like MOFs or metal hydrides.
  - 근거: corpus: Metal–organic frameworks (MOFs) are used for hydrogen storage due to their porous nature., corpus: Metal hydrides are classified into inter-metallic, complex, and lightweight hydrides for hydrogen storage.

## 분석 대상 특허의 범위
The scope of analysis for hydrogen storage technology patents includes inventions that specifically address the storage of hydrogen, whether through mechanical, chemical, or material-based methods. This includes technologies that improve storage efficiency, safety, and retrieval processes. Patents that focus on hydrogen production, utilization, or unrelated applications are excluded unless they directly contribute to or enable hydrogen storage.

## 범위 결정 (클러스터별 in/out)

- [IN] **Hydrogen storage materials** — These materials are directly involved in the storage of hydrogen, enhancing storage capacity and efficiency.
- [OUT] **Hydrogen production methods** — These methods focus on producing hydrogen, not storing it, unless they include a specific storage mechanism.
- [IN] **Hydrogen storage alloys** — These alloys are designed to store hydrogen, improving storage capacity and efficiency.
- [OUT] **Fuel cell systems** — Fuel cells utilize hydrogen but do not focus on the storage technology itself.
- [OUT] **Hydrogen generation systems** — These systems focus on generating hydrogen, not storing it, unless they include a specific storage mechanism.
- [IN] **Hydrogen storage systems** — These systems are directly involved in the storage of hydrogen.
- [CONDITIONAL] **Hydrogen purification methods** — In if the purification is part of a storage system; out if it is standalone or for non-storage purposes.
- [OUT] **Hydrogen refueling infrastructure** — Refueling infrastructure focuses on the delivery and use of hydrogen, not its storage technology.
- [IN] **Hydrogen storage tanks** — These tanks are specifically designed for storing hydrogen.
- [CONDITIONAL] **Hydrogen compression devices** — In if the compression is part of a storage system; out if it is standalone or for non-storage purposes.

## 제외 기준 (E)

- **E1.** Patents that focus on hydrogen production without detailing storage mechanisms are excluded.
  - 근거: corpus: Patents focusing on hydrogen production without detailing storage mechanisms, such as 'Method for producing hydrogen gas from marine algae using anaerobic microorganisms'.
- **E2.** Patents related to hydrogen usage in engines or other applications rather than storage technology are excluded.
  - 근거: corpus: Patents related to hydrogen usage in engines rather than storage technology, like 'Control method of air fuel ratio of hydrogen engine'.
- **E3.** Patents discussing safety during refueling rather than the technology of hydrogen storage itself are excluded.
  - 근거: corpus: Patents discussing safety during refueling rather than the technology of hydrogen storage itself, such as 'Driver interactive system for reducing the possibility of a static discharge during the refill of high pressure storage tanks in hydrogen fuel cell powered vehicles'.
- **E4.** Patents involving hydrogen in contexts like oil treatment or semiconductor manufacturing, which do not primarily address hydrogen storage, are excluded.
  - 근거: corpus: Patents involving hydrogen in contexts like oil treatment or semiconductor manufacturing, which do not primarily address hydrogen storage, such as 'Process for the treatment of crude oil using hydrogen in a special unit'.
- **E5.** Patents that are specific to hydrogen storage, not merely using hydrogen in a different context such as production or utilization, are excluded.
  - 근거: corpus: Hydrogen storage poses challenges due to its gaseous nature and ability to embrittle metals.

## 경계 판정 지침

- Patents focusing on hydrogen purification should be included only if the purification is part of a storage system, otherwise excluded.
- Hydrogen compression devices should be included if they are part of a storage system, otherwise excluded.

## 사용자 결정이 필요한 범위 질문

- **Q1. Should patents focusing on hydrogen purification be included if they are not directly linked to storage technology?**
  - 영향: 측정: 풀 표본 60건 중 37건(~62%)의 판정이 넓게/좁게에 따라 갈립니다. This determines whether purification methods that could indirectly support storage are included.
  - 선택지: Include all purification methods related to hydrogen., Include only purification methods that are part of a storage system.
  - 현재 가정(미답변 시): Include only purification methods that are part of a storage system.
- **Q2. Should hydrogen compression devices be included if they are not directly linked to storage technology?**
  - 영향: 측정: 풀 표본 60건 중 35건(~58%)의 판정이 넓게/좁게에 따라 갈립니다. This affects whether compression devices that could indirectly support storage are included.
  - 선택지: Include all compression devices related to hydrogen., Include only compression devices that are part of a storage system.
  - 현재 가정(미답변 시): Include only compression devices that are part of a storage system.
