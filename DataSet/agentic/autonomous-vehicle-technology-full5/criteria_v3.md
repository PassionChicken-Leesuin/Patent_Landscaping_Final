# 도메인 판단 기준서 — Autonomous Vehicle Technology

## 도메인 정의
Autonomous Vehicle Technology encompasses systems and methods that enable vehicles to operate without human intervention by navigating roads, detecting and responding to dynamic environmental conditions, ensuring passenger safety through collision avoidance, integrating with existing transportation infrastructure, and providing real-time decision-making capabilities for route optimization and obstacle management.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable a vehicle to navigate roads and traffic without human input, using technologies such as sensors, cameras, or GPS.
  - 근거: corpus: Autonomous Navigation and Path Planning, corpus: Sensor Integration for Autonomous Driving
- **C2.** The invention must include systems for detecting and responding to dynamic environmental conditions, such as pedestrians and other vehicles, using technologies like LiDAR, RADAR, or V2X communication.
  - 근거: corpus: Pedestrian Detection, corpus: Vehicle-to-Everything (V2X) Communication
- **C3.** The invention must incorporate collision avoidance systems that ensure passenger safety through technologies like forward collision prevention or lane keeping assistance.
  - 근거: corpus: Collision Avoidance Systems, corpus: Lane Keeping and Departure Systems
- **C4.** The invention must integrate with existing transportation infrastructure, such as traffic signals and road signs, potentially using V2I communication.
  - 근거: corpus: Vehicle-to-Infrastructure (V2I) Communication, corpus: Traffic Sign Recognition
- **C5.** The invention must provide real-time decision-making capabilities for route optimization and obstacle management, using technologies such as AI, machine learning algorithms, or real-time data processing systems.
  - 근거: corpus: Adaptive Motion Control, corpus: Machine Learning for Driving
- **C6.** The invention must perform obstacle detection and avoidance using technologies like sensors, cameras, or advanced algorithms.
  - 근거: corpus: Obstacle Detection and Avoidance, corpus: Sensor Integration for Autonomous Driving

## 분석 대상 특허의 범위
The scope of analysis for Autonomous Vehicle Technology includes patents that implement, improve, or provide enabling components or methods specific to autonomous vehicle systems. This includes technologies for navigation, environmental detection, collision avoidance, infrastructure integration, and real-time decision-making. Patents that merely use autonomous vehicle outputs or vocabulary for unrelated purposes are excluded.

## 범위 결정 (클러스터별 in/out)

- [OUT] **Cruise Control Systems** — Cruise control systems are not specific to autonomous vehicle technology as they do not enable full autonomy.
- [IN] **Traffic Sign Recognition** — Traffic sign recognition is essential for autonomous vehicles to integrate with existing transportation infrastructure.
- [IN] **Vehicle-to-Everything (V2X) Communication** — V2X communication is crucial for autonomous vehicles to interact with their environment and other vehicles.
- [IN] **Collision Avoidance Systems** — Collision avoidance systems are a core component of ensuring passenger safety in autonomous vehicles.
- [IN] **Sensor Cross-Validation** — Sensor cross-validation is important for accurate environmental detection and decision-making in autonomous vehicles.
- [IN] **Obstacle Detection and Avoidance** — Obstacle detection and avoidance are fundamental tasks for autonomous vehicle navigation.
- [CONDITIONAL] **Lane Departure Warning Systems** — In if the system is part of a broader autonomous driving system; out if it functions solely as a driver assistance feature.
- [IN] **Autonomous Navigation and Path Planning** — Autonomous navigation and path planning are central to the operation of autonomous vehicles.
- [CONDITIONAL] **Adaptive Driving Assistance** — In if it contributes to full autonomy; out if it only assists human drivers without enabling autonomy.
- [OUT] **Home Automation Integration** — Home automation integration focuses on non-vehicular tasks and does not contribute to vehicle autonomy.

## 제외 기준 (E)

- **E1.** Patents that focus on driver assistance systems that do not contribute to vehicle autonomy are excluded.
  - 근거: corpus: Adaptive Driving Assistance
- **E2.** Patents related to vehicle communication for purposes unrelated to autonomous driving, such as home automation, are excluded.
  - 근거: corpus: Home Automation Integration
- **E3.** Patents that pertain to autonomous control of non-land vehicles, such as ships or aircraft, are excluded.
  - 근거: corpus: Unmanned ship autopilot, corpus: Automatic approach landing and go-around pitch axis control system for aircraft

## 경계 판정 지침

- Lane Departure Warning Systems are in scope if they are integrated into a broader autonomous driving system, but out of scope if they function solely as a driver assistance feature.
- Adaptive Driving Assistance is in scope if it contributes to full autonomy, but out of scope if it only assists human drivers without enabling autonomy.
- Object Detection is in scope if it is used for autonomous navigation or obstacle avoidance, but out of scope if it is used for unrelated purposes.
- Traffic Lane Detection is in scope if it is part of an autonomous navigation system, but out of scope if it is used solely for driver assistance.

## 사용자 결정이 필요한 범위 질문

- **Q2. Should lane departure warning systems be included if they are not part of a broader autonomous system?**
  - 영향: 측정: 풀 표본 60건 중 26건(~43%)의 판정이 넓게/좁게에 따라 갈립니다. Clarifies the inclusion of systems that are standalone driver aids.
  - 선택지: Include all lane departure warning systems., Include only those integrated into autonomous systems.
  - 현재 가정(미답변 시): Include only those integrated into autonomous systems.
- **Q1. Does the domain include adaptive driving assistance systems that do not enable full autonomy?**
  - 영향: 측정: 풀 표본 60건 중 25건(~42%)의 판정이 넓게/좁게에 따라 갈립니다. Determines whether systems that assist but do not fully automate driving are included.
  - 선택지: Include all adaptive driving assistance systems., Include only those that contribute to full autonomy.
  - 현재 가정(미답변 시): Include only those that contribute to full autonomy.
