# 도메인 판단 기준서 — Autonomous Vehicle Technology

## 도메인 정의
Autonomous Vehicle Technology encompasses systems and methods that enable vehicles to operate without human intervention by autonomously navigating roads, detecting and responding to environmental conditions and obstacles, ensuring passenger safety through collision avoidance and emergency handling, integrating with traffic management systems for route optimization and compliance with traffic laws, and providing real-time data processing and decision-making capabilities for dynamic driving conditions. This includes the integration of machine learning and AI for enhanced decision-making and navigation.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable a vehicle to navigate roads and traffic autonomously without human input.
  - 근거: corpus: definition, corpus: task
- **C2.** The invention must include systems for detecting and responding to environmental conditions and obstacles.
  - 근거: corpus: technique, corpus: task
- **C3.** The invention must ensure passenger safety through collision avoidance and emergency handling.
  - 근거: corpus: task, corpus: technique
- **C4.** The invention must integrate with traffic management systems for route optimization and compliance with traffic laws.
  - 근거: corpus: technique, corpus: task
- **C5.** The invention must provide real-time data processing and decision-making capabilities for dynamic driving conditions.
  - 근거: corpus: technique, corpus: task
- **C6.** The invention must utilize machine learning and AI to enhance decision-making and navigation capabilities in autonomous vehicle systems.
  - 근거: corpus: technique, corpus: task
- **C7.** The invention must integrate V2X communication systems for vehicle-to-everything interactions, facilitating autonomous vehicle operations.
  - 근거: corpus: technique, corpus: task

## 분석 대상 특허의 범위
The scope of analysis for Autonomous Vehicle Technology includes patents that implement, improve, or provide enabling components or methods specific to autonomous vehicle systems. This includes technologies for autonomous navigation, environmental sensing, collision avoidance, traffic system integration, and real-time decision-making. Patents that merely use autonomous vehicle outputs or vocabulary for unrelated purposes are excluded.

## 범위 결정 (클러스터별 in/out)

- [IN] **Object detection systems** — Object detection systems are crucial for autonomous vehicles to identify and respond to environmental conditions and obstacles, fulfilling a core task of the domain.
- [IN] **Traffic sign recognition** — Traffic sign recognition is essential for autonomous vehicles to comply with traffic laws and integrate with traffic management systems.
- [CONDITIONAL] **Vehicle parking assistance** — Vehicle parking assistance is in scope if it enables autonomous parking without human intervention, otherwise out if it merely assists human drivers.
- [IN] **Collision avoidance systems** — Collision avoidance systems are integral to ensuring passenger safety, a defining task of autonomous vehicle technology.
- [IN] **Robotic driving status determination** — Robotic driving status determination is necessary for autonomous navigation and decision-making processes.
- [CONDITIONAL] **Driving assistance systems** — Driving assistance systems are in scope if they enable or enhance autonomous driving capabilities, otherwise out if they only assist human drivers.
- [IN] **Autonomous vehicle systems** — Autonomous vehicle systems directly implement the core tasks of autonomous navigation and operation without human intervention.
- [CONDITIONAL] **Sensor technologies for vehicles** — Sensor technologies are in scope if specifically designed for autonomous vehicle applications, otherwise out if generic.
- [IN] **V2X communication systems** — V2X communication systems are essential for integrating autonomous vehicles with traffic management systems and other vehicles.
- [IN] **Pedestrian detection methods** — Pedestrian detection methods are crucial for autonomous vehicles to safely navigate and avoid collisions with pedestrians.
- [CONDITIONAL] **Vehicle imaging systems** — Vehicle imaging systems are in scope if they are specifically used for autonomous navigation and environmental sensing.
- [IN] **Autonomous navigation systems** — Autonomous navigation systems are central to the domain, enabling vehicles to navigate without human input.
- [CONDITIONAL] **Vehicle communication systems** — Vehicle communication systems are in scope if they facilitate autonomous vehicle operations, otherwise out if generic.
- [CONDITIONAL] **Radar and sensor technologies** — Radar and sensor technologies are in scope if specifically tailored for autonomous vehicle applications.
- [CONDITIONAL] **Lane departure warning systems** — Lane departure warning systems are in scope if they contribute to autonomous driving capabilities by automatically correcting vehicle trajectory without human intervention.
- [CONDITIONAL] **Lane keeping assistance** — Lane keeping assistance is in scope if it autonomously maintains lane position without human input, otherwise out if it only assists human drivers.

## 제외 기준 (E)

- **E1.** Patents related to general sensor technologies not specific to autonomous vehicles are excluded.
  - 근거: corpus: boundary_case
- **E2.** Patents focused on non-vehicle related technologies, such as furniture design or medical rehabilitation, are excluded.
  - 근거: corpus: boundary_case
- **E3.** Patents involving general control systems are excluded unless they are specifically adapted or applied to autonomous vehicle technology.
  - 근거: corpus: boundary_case
- **E4.** Patents on general imaging or camera systems are excluded unless they are specifically adapted or applied to vehicle applications.
  - 근거: corpus: boundary_case

## 경계 판정 지침

- For 'Vehicle parking assistance', include if the system enables autonomous parking without human intervention.
- For 'Driving assistance systems', include if the system enhances or enables autonomous driving capabilities.
- For 'Sensor technologies for vehicles', include if the sensors are specifically designed for autonomous vehicle applications.
- For 'Vehicle imaging systems', include if the imaging is used for autonomous navigation and environmental sensing.
- For 'Vehicle communication systems', include if the communication facilitates autonomous vehicle operations.
- For 'Lane departure warning systems', include if they contribute to autonomous driving by automatically correcting vehicle trajectory.
- For 'Lane keeping assistance', include if it autonomously maintains lane position without human input.
