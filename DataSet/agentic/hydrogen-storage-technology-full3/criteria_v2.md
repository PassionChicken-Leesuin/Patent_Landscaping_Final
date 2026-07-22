# 도메인 판단 기준서 — Hydrogen Storage Technology

## 도메인 정의
Hydrogen Storage Technology encompasses inventions that enable the storage of hydrogen in a stable and efficient manner, ensuring its safe containment and controlled release for subsequent use. This includes methods and systems that optimize the volume and weight efficiency of hydrogen storage, such as through compression, liquefaction, or chemical bonding, and are compatible with existing hydrogen infrastructure. The technology must specifically address the challenges of maintaining hydrogen in a usable form under various conditions, facilitating its use in applications ranging from vehicular fuel to industrial processes.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the storage of hydrogen in a stable form, evidenced by mechanisms such as compression, liquefaction, or chemical bonding mentioned in the title or abstract.
  - 근거: corpus: Hydrogen storage methods include mechanical approaches like high pressures and low temperatures, and chemical compounds that release H2 on demand.
- **C2.** The invention must allow for the efficient release of hydrogen when needed, with specific release mechanisms like electrochemical or thermal processes mentioned in the title or abstract.
  - 근거: corpus: Electrochemical hydrogen storage allows controlled release of hydrogen using electricity., corpus: Hydrogen can be converted back to electrical power using a fuel cell or hydrogen turbine.
- **C3.** The invention must ensure the safety of hydrogen storage under various conditions, preventing leaks or explosions.
  - 근거: corpus: Hydrogen storage in vehicles requires storing hydrogen in an energy-dense form for sufficient driving range., corpus: Liquid hydrogen must be cooled below its critical point of 33 K to exist as a liquid.
- **C4.** The invention must optimize the volume and weight efficiency of hydrogen storage, making it practical for applications such as transportation or industrial use.
  - 근거: corpus: Storing hydrogen as a liquid takes less space than storing it as a gas at normal temperature and pressure., corpus: Nanomaterials can improve hydrogen storage by enhancing sorption kinetics and storage capacity.
- **C5.** The invention must be compatible with existing hydrogen infrastructure, such as integration with pipelines or refueling stations, as evident in the title or abstract.
  - 근거: corpus: Hydrogen technologies can be carbon neutral and may help prevent climate change.

## 분석 대상 특허의 범위
The scope of analysis for Hydrogen Storage Technology includes patents that specifically address the storage of hydrogen in a stable, efficient, and safe manner, with a focus on methods and systems that facilitate its use in various applications. This includes technologies related to compression, liquefaction, chemical bonding, and other innovative storage solutions. Patents that merely involve hydrogen in contexts unrelated to storage, such as production, utilization, or unrelated chemical processes, are excluded.

## 범위 결정 (클러스터별 in/out)

- [IN] **Hydrogen storage materials** — These patents focus on materials specifically designed for storing hydrogen, which is a core task of the domain.
- [OUT] **Hydrogen production methods** — These patents focus on the production of hydrogen, not its storage, which is outside the domain's scope.
- [IN] **Hydrogen storage alloys** — These patents involve alloys specifically designed to store hydrogen, aligning with the domain's core purpose.
- [OUT] **Hydrogen generation systems** — These patents focus on generating hydrogen, not storing it, which is outside the domain's scope.
- [OUT] **Fuel cell technologies** — These patents focus on the utilization of hydrogen in fuel cells, not its storage.
- [CONDITIONAL] **Hydrogen refueling stations** — In if the technology specifically addresses the storage aspect within the refueling process; out if it focuses solely on refueling logistics.
- [IN] **Hydrogen storage systems** — These patents focus on systems specifically designed for storing hydrogen, which is a core task of the domain.
- [CONDITIONAL] **Hydrogen supply systems** — In if the supply system includes specific storage technology; out if it focuses solely on distribution logistics.
- [CONDITIONAL] **Hydrogen compressors** — In if the compressor is specifically designed for hydrogen storage purposes; out if it is a general-purpose compressor.
- [CONDITIONAL] **Hydrogen purification** — In if the purification process is integral to maintaining hydrogen quality for storage; out if it is a general purification process not specific to storage.
- [IN] **Hydrogen absorption and desorption** — These patents focus on the processes of absorbing and releasing hydrogen, which are integral to storage technology.
- [OUT] **Electrolysis systems** — These patents focus on producing hydrogen through electrolysis, not storing it.
- [OUT] **Hydrogenation processes** — These patents focus on chemical processes involving hydrogen, not its storage.
- [OUT] **Gas purification and separation** — These patents focus on purifying and separating gases, not specifically on hydrogen storage.

## 제외 기준 (E)

- **E1.** Patents that focus on hydrogen production methods without specific storage technology are excluded.
  - 근거: corpus: Patents focusing on hydrogen production without specific storage technology, such as 'Method for producing hydrogen gas from marine algae using anaerobic microorganisms'.
- **E2.** Patents related to fuel cells but not directly about hydrogen storage are excluded.
  - 근거: corpus: Patents related to fuel cells but not directly about hydrogen storage, like 'Air supply system used for fuel cell and capable of strengthening safety discharge of hydrogen gas'.
- **E3.** Patents discussing hydrogen utilization where storage is not a primary function are excluded.
  - 근거: corpus: Patents discussing hydrogen utilization rather than storage or generation, such as 'Hydrogen gas utilizing method'.
- **E4.** Patents pertaining to hydrogen engines where storage is not a primary function are excluded.
  - 근거: corpus: Patents pertaining to hydrogen engines, not directly to storage technology, like 'Control method of air fuel ratio of hydrogen engine'.
- **E5.** Patents involving hydrogen in a different context, such as semiconductor manufacturing or oil production, are excluded.
  - 근거: corpus: Patents discussing hydrogen in semiconductor manufacturing, not storage, such as 'Manufacture of semiconductor device'., corpus: Patents discussing hydrogen in the context of oil production, not storage, like 'Method for producing special lubricating oil base oil'.

## 경계 판정 지침

- For patents related to hydrogen refueling stations, include them if they specifically address storage technology within the refueling process, such as specific storage capacities or integration features.
- For hydrogen supply systems, include them if they incorporate specific storage technology, otherwise exclude.
- For hydrogen compressors, include them if they are specifically designed for hydrogen storage purposes, otherwise exclude.
