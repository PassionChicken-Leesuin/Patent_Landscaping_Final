# 도메인 판단 기준서 — Autonomous Vehicle Technology

## 도메인 정의
Autonomous Vehicle Technology encompasses systems and methods that enable vehicles to operate independently without human intervention. This includes the ability to navigate roads and traffic autonomously, detect and respond to dynamic environmental conditions such as other vehicles, pedestrians, and road signs, ensure passenger safety through collision avoidance and emergency handling systems, integrate with mapping and GPS systems for optimal route determination, utilize vehicle-to-vehicle and vehicle-to-infrastructure communication to enhance situational awareness, and employ AI or machine learning techniques for autonomous vehicle operation.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable a vehicle to navigate roads and traffic autonomously without human input.
  - 근거: corpus: definition, corpus: task
- **C2.** The invention must include systems that detect and respond to dynamic environmental conditions, such as other vehicles, pedestrians, and road signs.
  - 근거: corpus: definition, corpus: technique
- **C3.** The invention must ensure passenger safety through collision avoidance and emergency handling systems.
  - 근거: corpus: task, corpus: technique
- **C4.** The invention must integrate with mapping and GPS systems to determine optimal routes for autonomous navigation.
  - 근거: corpus: technique, corpus: task
- **C5.** The invention must include vehicle-to-vehicle and vehicle-to-infrastructure communication systems to enhance situational awareness.
  - 근거: corpus: definition, corpus: technique
- **C6.** The invention must utilize AI or machine learning techniques for autonomous vehicle operation.
  - 근거: corpus: technique, corpus: definition

## 분석 대상 특허의 범위
The scope of analysis for Autonomous Vehicle Technology includes patents that specifically enable vehicles to operate independently without human intervention. This encompasses technologies for autonomous navigation, environmental detection and response, safety systems, integration with mapping and GPS, communication systems that enhance situational awareness, and the use of AI or machine learning for autonomous operation. Patents that merely assist human drivers or relate to non-transportation autonomous systems are excluded.

## 범위 결정 (클러스터별 in/out)

- [OUT] **Cruise Control Systems** — Cruise control systems assist human drivers rather than enabling full autonomy.
- [IN] **Traffic Sign Recognition** — Traffic sign recognition is essential for autonomous vehicles to navigate and respond to road conditions.
- [IN] **Vehicle-to-Everything (V2X) Communication** — V2X communication enhances situational awareness, a key component of autonomous vehicle operation.
- [IN] **Collision Avoidance Systems** — Collision avoidance is crucial for ensuring passenger safety in autonomous vehicles.
- [CONDITIONAL] **Sensor Cross-Validation** — In if used for autonomous navigation and environmental detection; out if used for non-autonomous purposes.
- [IN] **Obstacle Detection and Avoidance** — Obstacle detection and avoidance are fundamental for autonomous navigation.
- [OUT] **Lane Departure Warning Systems** — Lane departure warning systems assist human drivers rather than enabling full autonomy.
- [IN] **Autonomous Navigation and Path Planning** — Autonomous navigation and path planning are core tasks of autonomous vehicles.
- [OUT] **Adaptive Driving Assistance** — Adaptive driving assistance enhances human driving rather than replacing it with autonomy.
- [IN] **Hazard Detection Systems** — Hazard detection is necessary for autonomous vehicles to respond to dynamic environments.
- [IN] **Object Detection** — Object detection is essential for autonomous vehicles to navigate and avoid collisions.
- [IN] **Traffic Lane Detection** — Traffic lane detection is necessary for autonomous navigation and maintaining lane position.
- [IN] **Pedestrian Detection** — Pedestrian detection is crucial for ensuring safety in autonomous vehicle operation.
- [IN] **Autonomous Vehicle Control** — Autonomous vehicle control is a defining task of the domain.
- [CONDITIONAL] **Vehicle Communication Systems** — In if specifically for enhancing autonomous vehicle situational awareness; out if for general communication.
- [CONDITIONAL] **Image Processing for Vehicles** — In if used for autonomous navigation and environmental detection; out if for non-autonomous purposes.
- [OUT] **Driving Preference Adaptation** — Driving preference adaptation assists human drivers rather than enabling full autonomy.
- [CONDITIONAL] **Adaptive Motion Control** — In if used for autonomous vehicle navigation and control; out if for non-autonomous vehicle control.
- [OUT] **Driving Assistance Systems** — Driving assistance systems enhance human driving rather than replacing it with autonomy.
- [IN] **Pedestrian Detection Methods** — Pedestrian detection is crucial for ensuring safety in autonomous vehicle operation.
- [IN] **Vehicle Navigation Systems** — Vehicle navigation systems are essential for autonomous route planning and execution.
- [IN] **V2V Communication** — V2V communication enhances situational awareness, a key component of autonomous vehicle operation.
- [OUT] **Lane Keeping and Departure Systems** — Lane keeping and departure systems assist human drivers rather than enabling full autonomy.
- [OUT] **Driver Intent Prediction** — Driver intent prediction assists human drivers rather than enabling full autonomy.
- [CONDITIONAL] **3D Point Cloud Generation** — In if used for autonomous navigation and environmental mapping; out if for non-autonomous purposes.
- [IN] **Self-Driving Vehicle Allocation** — Self-driving vehicle allocation is part of managing autonomous vehicle fleets.
- [IN] **High Definition Map Updating** — High definition map updating is essential for autonomous navigation.
- [CONDITIONAL] **Radar Systems for Vehicles** — In if used for autonomous navigation and environmental detection; out if for non-autonomous purposes.
- [IN] **Remote Assistance for Autonomous Vehicles** — Remote assistance supports autonomous vehicle operation in complex scenarios.
- [OUT] **Driving Behavior Analysis** — Driving behavior analysis assists human drivers rather than enabling full autonomy.
- [CONDITIONAL] **Vehicle Data Acquisition** — In if used for autonomous vehicle operation; out if for general data acquisition.
- [OUT] **Driver Assist Systems** — Driver assist systems enhance human driving rather than replacing it with autonomy.
- [IN] **Cloud-Based Mapping for Vehicles** — Cloud-based mapping supports autonomous navigation and route planning.
- [IN] **Indoor Self-Driving Vehicle Positioning** — Indoor positioning is relevant for autonomous vehicle operation in controlled environments.
- [CONDITIONAL] **Smart Parking Systems** — In if specifically for autonomous vehicle parking; out if for general parking assistance.
- [CONDITIONAL] **Radar Technology for Vehicles** — In if used for autonomous navigation and environmental detection; out if for non-autonomous purposes.
- [OUT] **Parking Assistance Technology** — Parking assistance technology assists human drivers rather than enabling full autonomy.
- [OUT] **Electric Vehicle Technology** — Electric vehicle technology is not specific to autonomous operation.
- [CONDITIONAL] **Network Synchronization Methods** — In if used for autonomous vehicle communication; out if for general network purposes.
- [CONDITIONAL] **Automated Control Systems** — In if specifically for autonomous vehicle operation; out if for general automation.
- [CONDITIONAL] **Transportation Systems** — In if specifically for autonomous vehicle operation; out if for general transportation.
- [CONDITIONAL] **Vehicle Control Systems** — In if specifically for autonomous vehicle operation; out if for general vehicle control.
- [CONDITIONAL] **Signal Detection and Processing** — In if used for autonomous navigation and environmental detection; out if for non-autonomous purposes.
- [OUT] **Automated Machinery** — Automated machinery is not specific to autonomous vehicle operation.
- [OUT] **Energy-Efficient Devices** — Energy-efficient devices are not specific to autonomous vehicle operation.
- [CONDITIONAL] **Data Management Systems** — In if used for autonomous vehicle operation; out if for general data management.
- [CONDITIONAL] **Radar Tracking Systems** — In if used for autonomous navigation and environmental detection; out if for non-autonomous purposes.
- [OUT] **Vehicle Door Mechanisms** — Vehicle door mechanisms are not specific to autonomous vehicle operation.
- [OUT] **Emergency Call Location Systems** — Emergency call location systems are not specific to autonomous vehicle operation.
- [IN] **Obstacle Detection Systems** — Obstacle detection is fundamental for autonomous navigation.
- [CONDITIONAL] **Parking Space Detection** — In if specifically for autonomous vehicle parking; out if for general parking assistance.
- [IN] **Vehicle Navigation and Mapping** — Navigation and mapping are essential for autonomous vehicle operation.
- [CONDITIONAL] **Sensor Integration for Vehicles** — In if used for autonomous navigation and environmental detection; out if for non-autonomous purposes.
- [OUT] **Driver Assistance Technologies** — Driver assistance technologies enhance human driving rather than replacing it with autonomy.
- [OUT] **Unmanned Aerial Vehicles** — Unmanned aerial vehicles are not specific to land-based autonomous vehicle operation.
- [CONDITIONAL] **Distance Measurement Technologies** — In if used for autonomous navigation and environmental detection; out if for non-autonomous purposes.
- [CONDITIONAL] **Vehicle Management Systems** — In if specifically for autonomous vehicle operation; out if for general vehicle management.
- [CONDITIONAL] **Sensor Technologies** — In if used for autonomous navigation and environmental detection; out if for non-autonomous purposes.
- [CONDITIONAL] **Neural Networks** — In if used for autonomous vehicle operation; out if for general AI applications.
- [CONDITIONAL] **Traffic Monitoring** — In if specifically for autonomous vehicle operation; out if for general traffic monitoring.
- [IN] **Environment Mapping** — Environment mapping is essential for autonomous navigation.
- [OUT] **Trailer Hitch Assistance** — Trailer hitch assistance is not specific to autonomous vehicle operation.
- [IN] **Sensor Fusion** — Sensor fusion is crucial for accurate perception in autonomous vehicles.
- [CONDITIONAL] **Video Monitoring Systems** — In if used for autonomous navigation and environmental detection; out if for non-autonomous purposes.
- [IN] **Path Planning** — Path planning is a core task of autonomous vehicle operation.
- [IN] **Environment Perception** — Environment perception is essential for autonomous navigation and safety.

## 제외 기준 (E)

- **E1.** Patents that focus on driver assistance systems rather than full autonomy are excluded.
  - 근거: corpus: task, corpus: technique
- **E2.** Patents related to non-transportation autonomous systems, such as industrial robots or unmanned marine vehicles, are excluded.
  - 근거: corpus: boundary_case, corpus: task
- **E3.** Patents that address general vehicle components or systems without specific application to autonomous operation are excluded. Examples include seat adjustment mechanisms and non-autonomous control systems.
  - 근거: corpus: task, corpus: technique

## 경계 판정 지침

- Patents related to home automation systems communicating with vehicles are out unless they specifically enhance autonomous vehicle operation.
- Patents involving unmanned marine vehicles are out as they do not pertain to land-based autonomous vehicles.
- Patents about autonomous robots in non-transportation fields are out unless they specifically apply to autonomous vehicles for transportation.
- Patents focused on driver assistance rather than full autonomy are out as they enhance human driving rather than replacing it.
- Patents related to aircraft control systems are out as they do not apply to ground vehicles.
- Patents involving general vehicle components or systems are out unless they specifically address autonomous functions.
- Patents utilizing AI-driven approaches for autonomous vehicle operation are in, as AI and machine learning are key components of modern autonomous vehicle technology.
