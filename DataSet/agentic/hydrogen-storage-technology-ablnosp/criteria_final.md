# 도메인 판단 기준서 — Hydrogen Storage Technology

## 도메인 정의
Hydrogen Storage Technology encompasses inventions that enable the storage of hydrogen in a stable and efficient manner, ensuring its safe containment and release when needed. These technologies must optimize the volume and weight efficiency of storage systems and be compatible with existing hydrogen infrastructure, focusing on methods such as mechanical compression, cryogenic liquid storage, chemical bonding, and advanced materials like metal hydrides and metal-organic frameworks.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the storage of hydrogen in a stable form, such as through compression, liquefaction, or chemical bonding.
  - 근거: https://en.wikipedia.org/wiki/Hydrogen_storage, https://www.energy.gov/eere/fuelcells/hydrogen-storage
- **C2.** The invention must allow for the efficient release of hydrogen when needed, ensuring that the stored hydrogen can be accessed and utilized effectively.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919310025
- **C3.** The invention must ensure the safety of hydrogen storage under various conditions, addressing risks such as leaks, pressure changes, and temperature fluctuations.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919310025
- **C4.** The invention must optimize the volume and weight efficiency of hydrogen storage, making it suitable for applications such as transportation and portable energy systems.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919310025
- **C5.** The invention must be compatible with existing hydrogen infrastructure, facilitating integration into current systems for hydrogen distribution and use.
  - 근거: https://www.energy.gov/eere/fuelcells/hydrogen-storage, https://www.sciencedirect.com/science/article/pii/S0360319919310025
- **C6.** The invention must enhance hydrogen storage capacity or efficiency through the use of advanced materials, such as Metal–Organic Frameworks (MOFs).
  - 근거: https://www.sciencedirect.com/science/article/pii/S0360319919310025, https://en.wikipedia.org/wiki/Metal%E2%80%93organic_framework

## 분석 대상 특허의 범위
The scope of analysis for Hydrogen Storage Technology includes patents that focus on the methods and materials for storing hydrogen in a stable, efficient, and safe manner. This includes technologies related to mechanical compression, cryogenic storage, chemical storage systems, and advanced materials like metal hydrides and metal-organic frameworks. Patents that primarily address hydrogen generation, utilization, or unrelated technologies are outside the scope.

## 범위 결정 (클러스터별 in/out)

- [IN] **Hydrogen storage alloys** — These alloys are directly related to the storage of hydrogen, focusing on materials that can absorb and release hydrogen efficiently.
- [OUT] **Hydrogen generation systems** — These systems focus on producing hydrogen rather than storing it, which is outside the scope of hydrogen storage technology.
- [OUT] **Hydrogen fuel cells** — Fuel cells are primarily concerned with the utilization of hydrogen for energy, not its storage.
- [IN] **Hydrogen storage materials** — These materials are central to the domain, focusing on the development of new materials for efficient hydrogen storage.
- [OUT] **Hydrogen recovery systems** — While related to hydrogen, recovery systems focus on reclaiming hydrogen from processes rather than storing it.
- [OUT] **Hydrogen production methods** — These methods are concerned with generating hydrogen, not storing it.
- [IN] **Hydrogen separation technologies** — Separation technologies can be integral to the storage process by purifying hydrogen for storage, aligning with the domain's focus on storage efficiency.

## 제외 기준 (E)

- **E1.** Patents that focus on hydrogen generation or production methods without addressing storage are excluded.
  - 근거: corpus: Hydrogen generation systems
- **E2.** Patents that primarily address the utilization of hydrogen, such as in fuel cells, are excluded unless they also address storage.
  - 근거: corpus: Hydrogen fuel cells
- **E3.** Patents related to hydrogen recovery or separation that do not involve storage are excluded.
  - 근거: corpus: Hydrogen recovery systems, corpus: Hydrogen separation technologies

## 경계 판정 지침

- Patents like 'Vehicle-mounted hydrogen supply system frame for hydrogen fuel logistics vehicle' are excluded as they focus on logistics rather than storage technology itself.
- Patents mentioning hydrogen in contexts unrelated to storage, such as 'Semiconductor manufacturing apparatus,' should be excluded as they do not address the core tasks of hydrogen storage technology.
- Technologies that involve hydrogen separation should be included if they are part of the storage process, enhancing storage efficiency or capacity.
- Liquid hydrogen storage technologies should be included if they enhance storage efficiency or capacity, as they are significant in web evidence.
