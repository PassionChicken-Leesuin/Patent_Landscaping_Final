# 도메인 판단 기준서 — Hydrogen Storage Technology

## 도메인 정의
Hydrogen Storage Technology encompasses methods and systems specifically designed to store hydrogen in a stable and efficient manner, allowing for its safe retrieval and use in energy applications. This includes technologies that enhance the storage density of hydrogen, maintain its purity, and ensure safety during storage and retrieval processes. The domain covers mechanical, chemical, and material-based approaches that are specifically tailored to address the challenges of hydrogen's small molecular size and its tendency to escape from containers.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable the storage of hydrogen in a stable form, either through mechanical means such as compression or liquefaction, or through chemical means such as metal hydrides or chemical compounds that release hydrogen on demand.
  - 근거: corpus: technique
- **C2.** The invention must facilitate the retrieval of hydrogen for use in energy applications, ensuring that hydrogen can be efficiently extracted from its storage medium.
  - 근거: corpus: task
- **C3.** The invention must incorporate safety measures specific to hydrogen storage, addressing risks such as leakage or explosion due to hydrogen's small molecular size and flammability.
  - 근거: corpus: task
- **C4.** The invention must optimize the volume or weight efficiency of hydrogen storage, potentially through advanced materials like metal-organic frameworks (MOFs) or nanomaterials that enhance storage capacity.
  - 근거: corpus: technique
- **C5.** The invention must maintain the purity of hydrogen during storage, preventing contamination that could affect its use in sensitive applications like fuel cells.
  - 근거: corpus: task

## 분석 대상 특허의 범위
The scope of analysis for Hydrogen Storage Technology includes patents that specifically address the storage of hydrogen, focusing on methods and systems that enhance storage stability, efficiency, and safety. This encompasses mechanical, chemical, and material-based storage solutions, as well as enabling technologies that are integral to the storage process. Patents that merely involve hydrogen in non-storage contexts or focus solely on production or utilization without addressing storage are excluded.

## 범위 결정 (클러스터별 in/out)

- [IN] **Hydrogen storage materials** — These patents focus on materials specifically designed to store hydrogen, aligning with the core purpose of the domain.
- [IN] **Hydrogen storage alloys** — These patents involve alloys that are specifically used for hydrogen storage, thus performing a defining task of the domain.
- [OUT] **Hydrogen generation systems** — These patents focus on the production of hydrogen rather than its storage, which is outside the domain's scope.
- [OUT] **Hydrogen production methods** — These patents address the production of hydrogen, not its storage, and therefore do not perform a defining task of the domain.
- [OUT] **Fuel cell technologies** — These patents focus on the utilization of hydrogen in fuel cells, not on the storage of hydrogen itself.
- [IN] **Hydrogen storage systems** — These patents directly address systems designed for the storage of hydrogen, which is central to the domain.
- [CONDITIONAL] **Hydrogen refueling infrastructure** — In if the infrastructure includes specific storage solutions for hydrogen; out if it only addresses refueling logistics without storage technology.
- [OUT] **Hydrogen purification methods** — These patents focus on purifying hydrogen, not on storing it, which is outside the domain's scope.
- [IN] **Hydrogen compression devices** — These devices are integral to mechanical storage methods, such as compressed hydrogen storage, which is within the domain.

## 제외 기준 (E)

- **E1.** Patents that focus solely on hydrogen production methods without addressing storage are excluded from the domain.
  - 근거: corpus: task
- **E2.** Patents that involve hydrogen utilization in applications like fuel cells or industrial processes without focusing on storage are excluded.
  - 근거: corpus: task
- **E3.** Patents that involve hydrogen in non-storage contexts, such as in beverages or unrelated chemical processes, are excluded.
  - 근거: corpus: task

## 경계 판정 지침

- Patents focusing on hydrogen production without addressing storage, such as those using marine algae, are out of scope as they do not perform a storage task.
- Patents related to safety during hydrogen refueling are conditional; they are in if they include specific storage solutions, otherwise out.
- Patents discussing hydrogen utilization in applications like ammonia production are out of scope as they do not focus on storage.
- Patents involving hydrogen in non-storage contexts, such as in beverages, are out of scope as they do not perform a storage task.
