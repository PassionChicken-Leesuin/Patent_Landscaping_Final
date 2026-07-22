# 도메인 판단 기준서 — 3D Printing Technology

## 도메인 정의
3D Printing Technology, also known as additive manufacturing, involves the creation of three-dimensional objects by adding material layer by layer, guided by digital models or CAD files. This technology encompasses various methods and systems that enable the precise deposition, joining, or solidification of materials such as plastics, metals, ceramics, or biological substances, allowing for the production of complex geometries, customization, and rapid prototyping with minimal material waste compared to traditional manufacturing methods.

## 도메인 판단 기준 (C)

- **C1.** The invention must involve a process or system that creates three-dimensional objects by adding material layer by layer.
  - 근거: https://www.3dprintingmedia.network/what-is-3d-printing/, https://www.sciencedirect.com/science/article/pii/S2214860420301234
- **C2.** The invention must utilize digital models or CAD files to guide the 3D printing process.
  - 근거: https://www.3dprintingmedia.network/what-is-3d-printing/, https://www.sciencedirect.com/science/article/pii/S2214860420301234
- **C3.** The invention must be capable of using various materials such as plastics, metals, ceramics, or biological substances in the 3D printing process.
  - 근거: https://www.3dprintingmedia.network/what-is-3d-printing/, https://www.sciencedirect.com/science/article/pii/S2214860420301234
- **C4.** The invention must enable the production of complex geometries or customized objects that are difficult to achieve with traditional manufacturing methods.
  - 근거: https://www.3dprintingmedia.network/what-is-3d-printing/, https://www.sciencedirect.com/science/article/pii/S2214860420301234
- **C5.** The invention must contribute to the reduction of material waste compared to traditional manufacturing methods.
  - 근거: https://www.3dprintingmedia.network/what-is-3d-printing/, https://www.sciencedirect.com/science/article/pii/S2214860420301234

## 분석 대상 특허의 범위
The scope of analysis for 3D Printing Technology includes patents that describe methods, systems, or materials specifically designed for the additive manufacturing process, where material is added layer by layer to create three-dimensional objects. This includes innovations in printing techniques, material compositions specific to 3D printing, and applications that leverage the unique capabilities of 3D printing. Patents that merely use 3D printing outputs or vocabulary for unrelated purposes are excluded.

## 범위 결정 (클러스터별 in/out)

- [IN] **Additive Manufacturing Methods** — These methods are central to the domain as they describe the processes of creating objects layer by layer, which is the core of 3D printing technology.
- [IN] **3D Printing Systems** — These systems are integral to the domain as they encompass the machinery and software that enable the 3D printing process.
- [CONDITIONAL] **Material Compositions** — In if the compositions are specifically designed for use in 3D printing processes; out if they are generic materials not tailored for 3D printing.
- [IN] **Stereolithography** — This is a specific 3D printing technique that uses light to solidify layers of material, fitting within the domain.
- [IN] **Laser Sintering** — This technique involves fusing material particles layer by layer, aligning with the domain's core processes.
- [IN] **Powder Bed Fusion** — This is a method of 3D printing that involves fusing powder layers, directly related to the domain.
- [IN] **Bioprinting** — Bioprinting is a specialized application of 3D printing technology for creating biological structures, fitting within the domain.
- [IN] **Metal 3D Printing** — This involves the use of 3D printing techniques to create metal objects, which is a recognized part of the domain.
- [IN] **Multi-Material Printing** — This involves using multiple materials in a single 3D printing process, enhancing the technology's capabilities.
- [IN] **Temperature Control in 3D Printing** — Temperature control is crucial for the quality and precision of 3D printed objects, making it relevant to the domain.
- [OUT] **Adhesive Surfaces** — These patents focus on surface properties rather than the creation of 3D objects, which is outside the domain.
- [CONDITIONAL] **Monitoring Systems** — In if the systems are specifically designed to monitor and improve the 3D printing process; out if they are generic monitoring systems.
- [OUT] **Origami Techniques** — These techniques do not involve additive manufacturing processes and are unrelated to 3D printing.
- [CONDITIONAL] **Orthodontic Applications** — In if the applications specifically involve 3D printing technology; out if they are generic orthodontic methods.
- [OUT] **Imaging and Display Technologies** — These technologies do not involve the additive manufacturing process and are unrelated to 3D printing.
- [OUT] **Photolithography Systems** — These systems are related to semiconductor manufacturing and do not involve 3D printing processes.
- [OUT] **Material Compositions without 3D Printing Applications** — These compositions are not specific to 3D printing and do not contribute to the domain.
- [OUT] **Non-3D Printing Manufacturing Methods** — These methods do not involve additive manufacturing processes and are unrelated to 3D printing.
- [CONDITIONAL] **Control Systems** — In if the systems are specifically designed for 3D printing processes; out if they are generic control systems.
- [OUT] **Semiconductor Manufacturing Processes** — These processes do not involve 3D printing technology and are unrelated to the domain.
- [OUT] **Medical Devices Not Related to 3D Printing** — These devices do not involve 3D printing technology and are unrelated to the domain.
- [OUT] **Traditional Manufacturing Processes** — These processes do not involve additive manufacturing and are unrelated to 3D printing.
- [OUT] **Construction Methods Not Related to 3D Printing** — These methods do not involve 3D printing technology and are unrelated to the domain.
- [OUT] **Packaging Technology** — These technologies do not involve additive manufacturing processes and are unrelated to 3D printing.
- [OUT] **Purification Methods** — These methods do not involve 3D printing technology and are unrelated to the domain.
- [OUT] **Heat Exchange** — These processes do not involve additive manufacturing and are unrelated to 3D printing.
- [OUT] **Photolithography in Semiconductor Manufacturing** — These processes do not involve 3D printing technology and are unrelated to the domain.
- [OUT] **Imaging without 3D Printing Context** — These technologies do not involve additive manufacturing processes and are unrelated to 3D printing.
- [OUT] **Coating Processes** — These processes do not involve additive manufacturing and are unrelated to 3D printing.
- [OUT] **Material Preparation without 3D Printing Context** — These processes do not involve additive manufacturing and are unrelated to 3D printing.

## 제외 기준 (E)

- **E1.** Patents that focus on adhesive surfaces or coatings without creating 3D objects are excluded from the domain.
  - 근거: corpus: boundary_case
- **E2.** Patents that involve traditional manufacturing processes without specific application to 3D printing are excluded.
  - 근거: corpus: boundary_case
- **E3.** Patents related to photolithography or semiconductor manufacturing processes that do not involve 3D printing are excluded.
  - 근거: corpus: boundary_case
- **E4.** Patents discussing imaging or display technologies without direct application to 3D printing are excluded.
  - 근거: corpus: boundary_case
- **E5.** Patents focusing on material compositions without specific 3D printing applications are excluded.
  - 근거: corpus: boundary_case

## 경계 판정 지침

- For patents focusing on adhesive surfaces, the judge should exclude them unless they directly involve the creation of 3D objects using additive manufacturing processes.
- For monitoring systems, include them if they are specifically designed to enhance or monitor the 3D printing process; exclude if they are generic systems not tailored to 3D printing.
- For orthodontic applications, include them if they specifically involve 3D printing technology; exclude if they are generic orthodontic methods without a 3D printing context.
