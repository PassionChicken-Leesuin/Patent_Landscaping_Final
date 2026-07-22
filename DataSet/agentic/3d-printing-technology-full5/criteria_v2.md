# 도메인 판단 기준서 — 3D Printing Technology

## 도메인 정의
3D Printing Technology, also known as additive manufacturing, involves the creation of three-dimensional objects by adding material layer by layer, guided by digital models. This technology encompasses various methods and materials, including plastics, metals, ceramics, and biological materials, and is characterized by its ability to produce complex shapes, enable rapid prototyping, and allow for customization. It includes the entire process from pre-processing, through the build stage, to post-processing, and requires precise control over material deposition.

## 도메인 판단 기준 (C)

- **C1.** The invention must involve the creation of three-dimensional objects by adding material layer by layer.
  - 근거: https://www.ansi.org/, corpus: definition
- **C2.** The invention must utilize digital models to guide the 3D printing process.
  - 근거: https://www.ansi.org/, corpus: definition
- **C3.** The invention must include a mechanism for precise control over the deposition of material during the 3D printing process.
  - 근거: corpus: task, corpus: technique
- **C4.** The invention must be capable of using various materials such as plastics, metals, ceramics, or biological materials in the 3D printing process.
  - 근거: corpus: signal_term, corpus: technique
- **C5.** The invention must enable the production of complex shapes or geometries that are difficult to construct by traditional methods.
  - 근거: corpus: task
- **C6.** The invention must include or improve a component, method, or material that is specific to 3D printing technology.
  - 근거: corpus: technique, corpus: task

## 분석 대상 특허의 범위
The scope of analysis for 3D Printing Technology includes patents that implement, improve, or provide enabling components, methods, or materials specific to the creation of three-dimensional objects through additive manufacturing processes. This encompasses various 3D printing techniques, materials, and applications, as well as specific improvements or innovations in the technology. Patents that merely use the outputs of 3D printing for unrelated purposes or that focus on adjacent technologies without contributing to the core 3D printing process are excluded.

## 범위 결정 (클러스터별 in/out)

- [IN] **Additive Manufacturing Methods** — These methods are central to the domain as they describe the processes of creating objects layer by layer.
- [IN] **3D Printing Systems** — These systems are integral to the domain as they encompass the machinery and software used in 3D printing.
- [IN] **Material Compositions** — Material compositions specific to 3D printing are crucial for enabling the technology to function with various materials.
- [IN] **Stereolithography** — Stereolithography is a specific 3D printing technique and thus falls within the domain.
- [IN] **Powder Bed Fusion** — Powder bed fusion is a recognized 3D printing method and is included in the domain.
- [IN] **Metal 3D Printing** — Metal 3D printing is a specific application of 3D printing technology.
- [IN] **Bioprinting** — Bioprinting is a specialized form of 3D printing involving biological materials.
- [IN] **Composite Materials** — Composite materials specific to 3D printing are included as they enable the technology to function with advanced materials.
- [IN] **Laser Additive Manufacturing** — Laser additive manufacturing is a technique used in 3D printing and is included in the domain.
- [IN] **Multi-Material Printing** — Multi-material printing is a capability of 3D printing technology and is included in the domain.
- [OUT] **Photolithography and Semiconductor Manufacturing** — These focus on semiconductor processes not specific to 3D printing technology.
- [IN] **3D Concrete Printing** — 3D concrete printing is a specific application of 3D printing technology in construction.
- [IN] **Fused Deposition Modeling (FDM)** — FDM is a common 3D printing process and is included in the domain.

## 제외 기준 (E)

- **E1.** Patents that focus on adhesive bonding surfaces without creating 3D printed objects directly are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E2.** Patents that discuss monitoring and identifying deficiencies without contributing to the core 3D printing process are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E3.** Patents involving recycling materials without directly pertaining to the creation of new 3D printed objects are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E4.** Patents that mention 3D printing but focus on integrating electronic devices rather than traditional 3D printing of objects are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E5.** Patents that involve 3D modeling but focus on surgical instruments rather than 3D printing technology itself are excluded.
  - 근거: corpus: suspected_boundary_cases

## 경계 판정 지침

- Patents focusing on adhesive bonding surfaces are excluded unless they directly involve the creation of 3D printed objects.
- Patents discussing monitoring and identifying deficiencies are excluded unless they contribute to the core 3D printing process.

## 사용자 결정이 필요한 범위 질문

- **Q1. Should patents that involve 3D printing but focus on biological support design be included in the domain?**
  - 영향: 측정: 풀 표본 60건 중 14건(~23%)의 판정이 넓게/좁게에 따라 갈립니다. This determines whether the domain includes specialized applications of 3D printing in biological contexts.
  - 선택지: Include biological support design as part of 3D printing technology., Exclude biological support design from 3D printing technology.
  - 현재 가정(미답변 시): Exclude biological support design from 3D printing technology.
