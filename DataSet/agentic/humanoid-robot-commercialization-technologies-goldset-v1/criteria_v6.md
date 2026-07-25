# 특허 도메인 판단 기준서 — Humanoid Robot Commercialization Technologies

## 도메인 정의

The domain of Humanoid Robot Commercialization Technologies encompasses inventions that enable or enhance the commercialization of humanoid robots, specifically those with bipedal locomotion and human-like features. This includes technologies that facilitate full-body control and balance, advanced manipulation capabilities, learning and control of multi-joint manipulation, joint actuators and reducers, robot vision and imitation learning, and safe human-robot collaboration. The domain excludes technologies specific to industrial processes, surgical robots, wearable exoskeletons, cleaning robots, logistics transport, and toys unless they directly contribute to humanoid robot functionalities.

## 기술축

### A1. Full-Body Control and Balance [core/high]

Technologies enabling full-body control and balance in humanoid robots, including bipedal locomotion and whole-body dynamics.

- 사용자 문서 명시: True
특허 풀 관찰: True
판단 근거: Full-body control and balance are essential for humanoid robots to perform tasks in dynamic environments, aligning with both user query and owner documentation.
- 출처:
  - [user_query/high] query.json: The technology must enable full-body control and balance in humanoid robots.
  - [owner_doc/high] local://A2_도메인설명.md#chunk0: Humanoid robots integrate mobility, manipulation, control, and AI into a human-like system.
  - [corpus/high] corpus:case:1: Humanoid robot control methods

### A2. Advanced Manipulation Capabilities [core/high]

Technologies facilitating advanced manipulation capabilities, including robotic hands, grippers, and tactile sensing.

- 사용자 문서 명시: True
특허 풀 관찰: True
판단 근거: Advanced manipulation is critical for humanoid robots to interact with their environment effectively, supported by both user query and owner documentation.
- 출처:
  - [user_query/high] query.json: The technology must facilitate advanced manipulation capabilities, including robotic hands and tactile sensing.
  - [owner_doc/high] local://A2_도메인설명.md#chunk0: Key technologies for humanoid robots include manipulation, control, and AI-based learning.
  - [corpus/high] corpus:case:2: Robotic manipulation and control

### A3. Learning and Control of Multi-Joint Manipulation [core/high]

Technologies involving learning and control of multi-joint manipulation, including motion planning and force control.

- 사용자 문서 명시: True
특허 풀 관찰: True
판단 근거: Multi-joint manipulation is a complex task requiring advanced learning and control techniques, essential for humanoid robots.
- 출처:
  - [user_query/high] query.json: The technology must involve learning and control of multi-joint manipulation.
  - [owner_doc/high] local://A2_판정규칙_v1.md: Learning-based grasping and manipulation, motion planning, force and impedance control are included.
  - [corpus/high] corpus:case:8: Robot learning and adaptation

### A4. Joint Actuators and Reducers [core/high]

Technologies including joint actuators and reducers, such as quasi-direct drive (QDD) and series elastic actuators (SEA).

- 사용자 문서 명시: True
특허 풀 관찰: True
판단 근거: Joint actuators and reducers are fundamental components for humanoid robot movement and control, as documented by the owner and observed in the corpus.
- 출처:
  - [user_query/high] query.json: The technology must include joint actuators and reducers, such as QDD and SEA.
  - [owner_doc/high] local://A2_판정규칙_v1.md: Joint actuators and reducers like QDD and SEA are core technologies.
  - [corpus/high] corpus:case:4: Humanoid robot technologies

### A5. Robot Vision and Imitation Learning [core/high]

Technologies supporting robot vision, vision-language-action (VLA) models, and imitation learning for humanoid robots.

- 사용자 문서 명시: True
특허 풀 관찰: True
판단 근거: Vision and imitation learning are critical for humanoid robots to perceive and learn from their environment, aligning with both user query and owner documentation.
- 출처:
  - [user_query/high] query.json: The technology must support robot vision, VLA, and imitation learning.
  - [owner_doc/high] local://KIMM_핵심자료_정리.md#chunk0: Vision-Language-Action (VLA) and End-to-End (E2E) neural networks are crucial for autonomous learning and generalization in humanoid robots.
  - [corpus/high] corpus:case:5: Robot control systems

### A6. Safe Human-Robot Collaboration [core/high]

Technologies ensuring safe human-robot collaboration, including collision detection and avoidance, and speed and separation monitoring.

- 사용자 문서 명시: True
특허 풀 관찰: True
판단 근거: Safe collaboration is essential for humanoid robots to operate alongside humans, supported by both user query and owner documentation.
- 출처:
  - [user_query/high] query.json: The technology must ensure safe human-robot collaboration.
  - [owner_doc/high] local://A2_판정규칙_v1.md: Human collaboration safety, including collision detection and avoidance, is a core technology.
  - [corpus/high] corpus:case:3: Collaborative robotic systems

## 포함 판단 기준 (C)

- **C1.** The invention must enable full-body control and balance in humanoid robots, including bipedal locomotion and whole-body dynamics, which are essential for performing complex tasks in dynamic environments, thereby enhancing their commercial viability.
  - 관찰 신호(비배타적 단서): bipedal locomotion, whole-body dynamics, balance control, humanoid robot, full-body control
  - 기술축: A1
  - [user_query/high] query.json: The technology must enable full-body control and balance in humanoid robots.
  - [owner_doc/high] local://A2_도메인설명.md#chunk0: Humanoid robots integrate mobility, manipulation, control, and AI into a human-like system.
  - [corpus/high] corpus:case:1: Humanoid robot control methods
  - 레거시 출처: query.json, local://A2_도메인설명.md#chunk0, corpus:case:1
- **C2.** The invention must facilitate advanced manipulation capabilities, including robotic hands, grippers, and tactile sensing, which are critical for humanoid robots to interact effectively with their environment, thus broadening their commercial applications.
  - 관찰 신호(비배타적 단서): robotic hands, grippers, tactile sensing, manipulation, humanoid robot
  - 기술축: A2
  - [user_query/high] query.json: The technology must facilitate advanced manipulation capabilities, including robotic hands and tactile sensing.
  - [owner_doc/high] local://A2_도메인설명.md#chunk0: Key technologies for humanoid robots include manipulation, control, and AI-based learning.
  - [corpus/high] corpus:case:2: Robotic manipulation and control
  - 레거시 출처: query.json, local://A2_도메인설명.md#chunk0, corpus:case:2
- **C3.** The invention must involve learning and control of multi-joint manipulation, including motion planning and force control, which are vital for humanoid robots to perform complex tasks autonomously, thereby increasing their market potential.
  - 관찰 신호(비배타적 단서): multi-joint manipulation, motion planning, force control, learning, humanoid robot
  - 기술축: A3
  - [user_query/high] query.json: The technology must involve learning and control of multi-joint manipulation.
  - [owner_doc/high] local://A2_판정규칙_v1.md: Learning-based grasping and manipulation, motion planning, force and impedance control are included.
  - [corpus/high] corpus:case:8: Robot learning and adaptation
  - 레거시 출처: query.json, local://A2_판정규칙_v1.md, corpus:case:8
- **C4.** The invention must include joint actuators and reducers, such as quasi-direct drive (QDD) and series elastic actuators (SEA), which are fundamental for precise and efficient humanoid robot movements, enhancing their commercial deployment.
  - 관찰 신호(비배타적 단서): joint actuators, reducers, QDD, SEA, humanoid robot
  - 기술축: A4
  - [user_query/high] query.json: The technology must include joint actuators and reducers, such as QDD and SEA.
  - [owner_doc/high] local://A2_판정규칙_v1.md: Joint actuators and reducers like QDD and SEA are core technologies.
  - [corpus/high] corpus:case:4: Humanoid robot technologies
  - 레거시 출처: query.json, local://A2_판정규칙_v1.md, corpus:case:4
- **C5.** The invention must support robot vision, vision-language-action (VLA) models, and imitation learning for humanoid robots, which are crucial for autonomous operation and adaptability in various commercial settings.
  - 관찰 신호(비배타적 단서): robot vision, VLA models, imitation learning, humanoid robot, learning
  - 기술축: A5
  - [user_query/high] query.json: The technology must support robot vision, VLA, and imitation learning.
  - [owner_doc/high] local://KIMM_핵심자료_정리.md#chunk0: Vision-Language-Action (VLA) and End-to-End (E2E) neural networks are crucial for autonomous learning and generalization in humanoid robots.
  - [corpus/high] corpus:case:5: Robot control systems
  - 레거시 출처: query.json, local://KIMM_핵심자료_정리.md#chunk0, corpus:case:5
- **C6.** The invention must ensure safe human-robot collaboration, including collision detection and avoidance, and speed and separation monitoring, which are essential for deploying humanoid robots in commercial environments where human interaction is frequent.
  - 관찰 신호(비배타적 단서): human-robot collaboration, collision detection, avoidance, speed monitoring, humanoid robot
  - 기술축: A6
  - [user_query/high] query.json: The technology must ensure safe human-robot collaboration.
  - [owner_doc/high] local://A2_판정규칙_v1.md: Human collaboration safety, including collision detection and avoidance, is a core technology.
  - [corpus/high] corpus:case:3: Collaborative robotic systems
  - 레거시 출처: query.json, local://A2_판정규칙_v1.md, corpus:case:3
- **C7.** The invention must integrate AI and cognitive sciences into humanoid robots, enhancing their decision-making, adaptability, and interaction capabilities, which are crucial for their commercial success.
  - 관찰 신호(비배타적 단서): AI integration, cognitive sciences, decision-making, adaptability, interaction capabilities
  - 기술축: A5
  - [user_query/high] query.json: The technology must integrate AI and cognitive sciences into humanoid robots.
  - [owner_doc/high] local://A2_도메인설명.md#chunk0: Humanoid robots integrate mobility, manipulation, control, and AI into a human-like system.
  - [corpus/high] corpus:mismatch:3: The web evidence emphasizes the importance of AI and cognitive sciences in humanoid robots.
  - 레거시 출처: query.json, local://A2_도메인설명.md#chunk0, corpus:mismatch:3

## 분석 대상 특허의 범위

The scope of analysis for Humanoid Robot Commercialization Technologies includes patents that implement, improve, or provide enabling components or methods specific to the commercialization of humanoid robots with bipedal locomotion and human-like features. This encompasses technologies for full-body control, advanced manipulation, learning and control of multi-joint manipulation, joint actuators and reducers, robot vision and imitation learning, and safe human-robot collaboration. Excluded are technologies for specific industrial processes, surgical robots, wearable exoskeletons, cleaning robots, logistics transport, and toys unless they directly contribute to humanoid robot functionalities.

## 범위 결정

- [IN] **robot control systems** — Patents in this cluster are included as they relate to control systems specific to humanoid robots, enabling full-body control and balance.
- [IN] **robotic manipulation** — This cluster is included as it involves advanced manipulation capabilities essential for humanoid robots.
- [IN] **humanoid robots** — This cluster is directly relevant to the domain as it focuses on humanoid robots and their commercialization.
- [CONDITIONAL] **robotic arms and end effectors** — Included if the robotic arms and end effectors are designed for humanoid robots, otherwise excluded if for general industrial use.
- [IN] **collaborative robots** — Included as they ensure safe human-robot collaboration, a core aspect of humanoid robot commercialization.
- [CONDITIONAL] **robotic grippers** — Included if the grippers are designed for humanoid robots, otherwise excluded if for niche applications.
- [IN] **robot safety systems** — Included as they ensure safe human-robot collaboration, which is essential for humanoid robots.
- [IN] **robotic learning and adaptation** — Included as it involves learning and control of multi-joint manipulation, crucial for humanoid robots.
- [CONDITIONAL] **robotic navigation and path planning** — [CONDITIONAL-IN] robotic navigation and path planning — INCLUDE general robot navigation: SLAM, obstacle avoidance, locomotion path planning, and navigation among humans in dynamic environments (owner doc KIMM lists 'SLAM·강화학습 자율 내비게이션' under the intelligence axis; general robot navigation transfers to humanoids). EXCLUDE only when the claims are bound to excluded platforms: floor-cleaning coverage paths or cleaner docking/recharge, and AGV/warehouse fleet routing or conveyor-synchronized transport. NOTE: the earlier wording 'excluded if for general robotics' is WRONG and must be replaced by this rule.
- [CONDITIONAL] **robotic assembly systems** — [CONDITIONAL-IN] robotic assembly — INCLUDE assembly CAPABILITY technology: force/impedance-controlled assembly, contact-rich assembly skill learning (RL + compliance), simulation-based assembly parameter tuning, bimanual assembly manipulation (humanoid deployment in factory assembly is a core commercialization path per owner docs: BMW/Figure, Mercedes/Apptronik). EXCLUDE assembly LINE EQUIPMENT: dedicated jigs, conveyor-synchronized assembly cells, welding/painting line integration, SMT/wafer process equipment. The test is claim scope (capability vs equipment), not the word 'assembly'.

## 제외 판단 기준 (E)

- **E1.** Patents that focus on specific industrial processes or equipment not directly contributing to humanoid robot functionalities are excluded.
  - 관찰 신호(비배타적 단서): industrial process, specific equipment, manufacturing, assembly, non-humanoid
  - [owner_doc/high] local://A2_판정규칙_v1.md: Specific industrial process technologies are excluded unless they directly contribute to humanoid robots.
  - 레거시 출처: local://A2_판정규칙_v1.md
- **E2.** Patents related to surgical robots, wearable exoskeletons, cleaning robots, logistics transport, and toys are excluded unless they directly contribute to humanoid robot functionalities.
  - 관찰 신호(비배타적 단서): surgical robot, wearable exoskeleton, cleaning robot, logistics transport, toy
  - [owner_doc/high] local://A2_판정규칙_v1.md: Technologies for surgical robots, exoskeletons, cleaning robots, logistics, and toys are excluded unless they contribute to humanoid robots.
  - 레거시 출처: local://A2_판정규칙_v1.md

## 경계 판정 지침

- Patents focusing on wearable robots are excluded unless they contribute to humanoid robot functionalities (corpus:boundary:1).
- Robotic devices for specific applications are excluded unless they serve humanoid robot functionalities (corpus:boundary:2).
- Industrial robot patents are excluded unless they have a humanoid context (corpus:boundary:3).
- Telepresence or VR-focused patents are excluded unless they contribute to humanoid robot commercialization (corpus:boundary:4).
- Patents on specific robotic applications are excluded unless they focus on humanoid functionalities (corpus:boundary:5).
