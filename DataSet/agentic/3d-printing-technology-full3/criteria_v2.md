# 도메인 판단 기준서 — 3D Printing Technology

## 도메인 정의
3D Printing Technology, also known as additive manufacturing, involves the creation of three-dimensional objects from digital models by adding material layer by layer. This technology must enable the precise control of material deposition to form objects with complex geometries and customizable features, using a variety of materials such as plastics, metals, or ceramics. The process typically includes stages of pre-processing, building, and post-processing, and is applicable across various fields including manufacturing, medicine, and construction.

## 도메인 판단 기준 (C)

- **C1.** The invention must involve a process that creates three-dimensional objects by adding material layer by layer based on a digital model.
  - 근거: https://en.wikipedia.org/wiki/3D_printing, https://www.sciencedirect.com/science/article/pii/S2214860420301234
- **C2.** The invention must include a method for precisely controlling the deposition of material to achieve the desired shape and properties of the object.
  - 근거: https://www.tandfonline.com/doi/full/10.1080/17452759.2020.1752713, https://www.sciencedirect.com/science/article/pii/S2214860420301234
- **C3.** The invention must be capable of using various materials such as plastics, metals, or ceramics in the 3D printing process.
  - 근거: https://www.sciencedirect.com/science/article/pii/S2214860420301234, https://en.wikipedia.org/wiki/3D_printing
- **C4.** The invention must allow for customization and rapid prototyping of complex geometries.
  - 근거: https://www.tandfonline.com/doi/full/10.1080/17452759.2020.1752713, https://en.wikipedia.org/wiki/3D_printing
- **C5.** The invention must include stages of pre-processing, building, and post-processing in the 3D printing process.
  - 근거: https://www.sciencedirect.com/science/article/pii/S2214860420301234, https://en.wikipedia.org/wiki/3D_printing

## 분석 대상 특허의 범위
The scope of analysis for 3D Printing Technology includes patents that describe methods, systems, or compositions specifically designed for the additive manufacturing process, where material is added layer by layer to create three-dimensional objects from digital models. This includes technologies applicable to various materials and industries, such as manufacturing, construction, and healthcare, but excludes patents that merely use 3D printing outputs or terminology without performing the core tasks of 3D printing.

## 범위 결정 (클러스터별 in/out)

- [IN] **Additive Manufacturing Methods** — These methods are central to the domain as they describe the processes of creating objects by adding material layer by layer.
- [IN] **3D Printing Systems** — These systems are integral to the domain as they encompass the machinery and software used to perform 3D printing.
- [CONDITIONAL] **Material Compositions** — In if the compositions are specifically formulated for use in 3D printing processes; out if they are general compositions without specific application to 3D printing.
- [IN] **Stereolithography** — This is a specific 3D printing technique that involves layer-by-layer construction using photopolymerization.
- [IN] **Metal 3D Printing** — This involves the use of metals in 3D printing processes, which is a recognized subset of the domain.
- [IN] **Bioprinting** — Bioprinting is a specialized form of 3D printing used to create biological structures, fitting within the domain.
- [IN] **Powder Bed Fusion** — This is a recognized 3D printing technique involving the fusion of powder materials layer by layer.
- [CONDITIONAL] **Composite Materials** — In if the composites are specifically designed for 3D printing applications; out if they are general composites without specific 3D printing relevance.
- [IN] **Laser Sintering** — This is a specific 3D printing technique involving the sintering of materials layer by layer.
- [IN] **Photopolymerization** — This technique is used in 3D printing processes like stereolithography, involving the curing of photopolymers layer by layer.
- [IN] **Rapid Prototyping** — Rapid prototyping is included as it often uses 3D printing technology to quickly fabricate parts for testing and development.

## 제외 기준 (E)

- **E1.** Patents that describe the use of 3D printing outputs or terminology for purposes unrelated to the additive manufacturing process are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E2.** Patents that focus on monitoring or auxiliary processes without detailing a specific 3D printing method are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E3.** Patents that describe components or materials without a clear link to 3D printing processes are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E4.** Patents that describe traditional manufacturing methods such as CNC machining, which do not involve additive processes, are excluded.
  - 근거: corpus: suspected_boundary_cases

## 경계 판정 지침

- Patents focusing on specific applications like orthodontics or lighting devices are out unless they detail a novel 3D printing method or system (e.g., 'Direct 3D-printed orthodontic aligners').
- Patents that involve monitoring or auxiliary processes are out unless they include a novel method integral to the 3D printing process (e.g., 'Method for automatic identification of material deposition deficiencies').
- Patents that mention 3D printing but focus on unrelated fields are out unless they detail a specific 3D printing method or application (e.g., 'Use of 3d printing for anticounterfeiting').
- Patents that describe components or materials are in only if they are specifically linked to 3D printing processes (e.g., 'Stabilized resin cross-linking agent').
- Patents involving monitoring or auxiliary processes are in only if they are essential to the 3D printing process, such as improving material deposition accuracy or quality control.
