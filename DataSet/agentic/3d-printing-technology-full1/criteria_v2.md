# 도메인 판단 기준서 — 3D Printing Technology

## 도메인 정의
3D Printing Technology, also known as additive manufacturing, involves the creation of three-dimensional objects by depositing material layer by layer based on digital models. This technology must interpret digital designs to guide the printing process, allowing for the production of complex geometries and customization. It utilizes various materials such as plastics, metals, ceramics, and biological substances, ensuring precision and accuracy in the layering process to achieve the desired object dimensions.

## 도메인 판단 기준 (C)

- **C1.** The invention must involve a process that creates three-dimensional objects by depositing material layer by layer based on digital model data.
  - 근거: https://www.ansi.org/, corpus: definition
- **C2.** The invention must be capable of interpreting digital models to guide the material deposition process.
  - 근거: corpus: task, corpus: definition
- **C3.** The invention must utilize materials such as plastics, metals, ceramics, or biological substances in the layer-by-layer deposition process of 3D printing.
  - 근거: corpus: signal_term, corpus: technique
- **C4.** The invention must allow for the customization and rapid prototyping of complex designs.
  - 근거: corpus: task, corpus: definition
- **C5.** The invention must ensure precision and accuracy in the layering process to achieve the desired object dimensions.
  - 근거: corpus: task, corpus: definition

## 분석 대상 특허의 범위
The scope of analysis for 3D Printing Technology includes patents that describe methods, systems, or compositions directly involved in the additive manufacturing process, where material is deposited layer by layer to create three-dimensional objects. This includes various techniques such as stereolithography, laser sintering, and bioprinting, as well as innovations in material compositions specifically designed for 3D printing. Patents that focus on peripheral or auxiliary processes, or that use 3D printing outputs for unrelated purposes, are outside the scope.

## 범위 결정 (클러스터별 in/out)

- [IN] **Additive Manufacturing Methods** — These methods are central to the domain as they describe the processes of creating objects layer by layer from digital models.
- [IN] **3D Printing Systems** — These systems are integral to the domain as they encompass the machinery and software that execute the 3D printing process.
- [IN] **Material Compositions** — Material compositions specifically designed for use in 3D printing are within scope as they enable the additive manufacturing process.
- [IN] **Stereolithography** — Stereolithography is a recognized 3D printing technique that fits the domain's definition of layer-by-layer object creation.
- [IN] **Laser Sintering** — Laser sintering is a key 3D printing technique involving layer-by-layer material fusion, aligning with the domain's core processes.
- [IN] **Powder Bed Fusion** — Powder bed fusion is a fundamental 3D printing method that constructs objects layer by layer, fitting the domain's criteria.
- [IN] **Bioprinting** — Bioprinting involves layer-by-layer construction of biological structures, directly aligning with the domain's definition.
- [IN] **Metal 3D Printing** — Metal 3D printing involves additive manufacturing processes using metals, fitting the domain's core purpose.
- [IN] **Composite Materials** — Composite materials designed for 3D printing are within scope as they are integral to the additive manufacturing process.
- [IN] **Multi-Material Printing** — Multi-material printing involves using different materials in a single 3D printing process, aligning with the domain's focus on material versatility.

## 제외 기준 (E)

- **E1.** Patents that focus on the use of 3D printing outputs for applications unrelated to the additive manufacturing process itself are excluded.
  - 근거: corpus: boundary_case
- **E2.** Patents that describe monitoring or auxiliary processes without directly contributing to the 3D printing process are excluded.
  - 근거: corpus: boundary_case
- **E3.** Patents that involve technologies like photolithography or semiconductor manufacturing, which are adjacent technologies due to their layer-based processing but do not align with the core 3D printing processes, are excluded.
  - 근거: corpus: mismatch_with_web_evidence

## 경계 판정 지침

- Patents focusing on specific applications like orthodontic aligners should be excluded unless they describe a novel 3D printing process or system integral to the domain. For example, if the patent introduces a new method of layer-by-layer deposition specific to aligners, it may be included.
- Patents discussing monitoring or auxiliary processes should be excluded unless they directly enhance the 3D printing process itself.
- Patents involving related but distinct technologies, such as digital lithography tools, should be excluded unless they directly pertain to additive manufacturing processes.
