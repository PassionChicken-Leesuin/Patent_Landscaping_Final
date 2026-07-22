# 도메인 판단 기준서 — Humanoid Robot Commercialization Technology

## 도메인 정의
Humanoid Robot Commercialization Technology encompasses the development and deployment of technologies that enable humanoid robots to be effectively and efficiently used in commercial settings. This includes systems that ensure safe and intuitive human-robot interaction, cost-effective production and maintenance, robust navigation and mobility in diverse environments, and compliance with regulatory and safety standards. The domain also covers the integration of humanoid robots into various industries, addressing challenges such as data scarcity, cybersecurity, and the establishment of supportive ecosystems for mass production and market viability.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable humanoid robots to perform tasks in real-world environments safely and efficiently.
  - 근거: corpus: task
- **C2.** The invention must include systems for human-robot interaction that are intuitive and reliable.
  - 근거: corpus: task
- **C3.** The invention must ensure the cost-effective production and maintenance of humanoid robots.
  - 근거: corpus: task
- **C4.** The invention must include robust navigation and mobility systems for humanoid robots in diverse settings.
  - 근거: corpus: task
- **C5.** The invention must address regulatory and safety standards for deploying humanoid robots in public and private sectors.
  - 근거: corpus: task

## 분석 대상 특허의 범위
The scope of analysis for Humanoid Robot Commercialization Technology includes patents that specifically contribute to the development, deployment, and commercialization of humanoid robots. This encompasses technologies that enhance the functionality, safety, and market readiness of humanoid robots, including their integration into various industries. Patents that merely use humanoid robots for unrelated purposes or lack specific contributions to their commercialization are excluded.

## 범위 결정 (클러스터별 in/out)

- [IN] **Robot control systems** — These systems are essential for the safe and efficient operation of humanoid robots in commercial environments.
- [IN] **Humanoid robot design** — Design innovations are crucial for the commercial viability and functionality of humanoid robots.
- [IN] **Robotic manipulation techniques** — Manipulation techniques are vital for humanoid robots to perform tasks in real-world settings.
- [CONDITIONAL] **Mobile robot systems** — In if the systems are specifically designed for humanoid robots; out if they are generic mobile systems without humanoid-specific features.
- [IN] **Human-robot interaction** — Intuitive and reliable interaction systems are key to the commercial deployment of humanoid robots.
- [IN] **Robotic arms and end effectors** — These components are critical for humanoid robots to perform complex tasks.
- [IN] **Robot safety mechanisms** — Safety mechanisms are necessary for the deployment of humanoid robots in public and private sectors.
- [IN] **Robot teaching and programming** — Teaching and programming systems are essential for adapting humanoid robots to various commercial applications.
- [OUT] **Wearable robotic systems** — These systems do not specifically contribute to humanoid robot commercialization.
- [CONDITIONAL] **Soft robotic actuators** — In if designed for humanoid robots; out if they are generic actuators without specific humanoid applications.
- [IN] **Robot navigation and mobility** — Robust navigation and mobility systems are crucial for humanoid robots in diverse environments.
- [CONDITIONAL] **Collaborative robots** — In if they include humanoid features and commercialization aspects; out if they are generic collaborative robots.
- [IN] **Robot calibration methods** — Calibration methods are important for ensuring the precision and reliability of humanoid robots.
- [IN] **Robotic sensors and feedback** — Sensors and feedback systems are essential for the functionality and safety of humanoid robots.
- [IN] **Robotic object manipulation** — Object manipulation capabilities are critical for humanoid robots to perform tasks in commercial settings.

## 제외 기준 (E)

- **E1.** Patents that focus on robotic systems without specific humanoid features or commercialization aspects are excluded.
  - 근거: corpus: suspected_boundary_cases
- **E2.** Patents that describe generic robotic applications not specifically related to humanoid robots are excluded.
  - 근거: corpus: suspected_boundary_cases

## 경계 판정 지침

- Patents focusing on cleaning robots are out unless they specifically address humanoid robot features or commercialization aspects.
- Patents describing industrial robots are out unless they include humanoid features or commercialization aspects.
- Patents on specific robotic applications are out unless they focus on humanoid capabilities.

## 사용자 결정이 필요한 범위 질문

- **Q1. Should patents on mobile robot systems be included if they are not specifically designed for humanoid robots?**
  - 영향: This determines whether generic mobile systems are considered part of the domain if they can be adapted for humanoid robots.
  - 선택지: Include all mobile robot systems that can be adapted for humanoid robots., Include only those specifically designed for humanoid robots.
  - 현재 가정(미답변 시): Include only those specifically designed for humanoid robots.
- **Q2. Should soft robotic actuators be included if they are not specifically designed for humanoid robots?**
  - 영향: This affects whether generic soft actuators are considered part of the domain if they can be used in humanoid robots.
  - 선택지: Include all soft robotic actuators that can be used in humanoid robots., Include only those specifically designed for humanoid robots.
  - 현재 가정(미답변 시): Include only those specifically designed for humanoid robots.
- **Q3. Should collaborative robots be included if they do not have specific humanoid features?**
  - 영향: This determines whether generic collaborative robots are part of the domain if they can be adapted for humanoid applications.
  - 선택지: Include all collaborative robots that can be adapted for humanoid applications., Include only those with specific humanoid features.
  - 현재 가정(미답변 시): Include only those with specific humanoid features.
