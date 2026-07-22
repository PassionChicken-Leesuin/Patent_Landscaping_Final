# 도메인 판단 기준서 — Autonomous Vehicle Technology

## 도메인 정의
Autonomous Vehicle Technology encompasses systems and methods that enable vehicles to navigate and operate on roads without human intervention. This includes technologies for perception, decision-making, and control that allow vehicles to detect and respond to dynamic environmental conditions, such as other vehicles, pedestrians, and road signs. The technology must ensure passenger safety through collision avoidance and emergency handling systems, integrate with existing transportation infrastructure like GPS and traffic management systems, and provide real-time data processing and decision-making capabilities to adapt to changing conditions.

## 도메인 판단 기준 (C)

- **C1.** The invention must enable a vehicle to navigate roads and traffic autonomously without human input.
  - 근거: corpus: definition
- **C2.** The invention must include systems for detecting and responding to dynamic environmental conditions, such as other vehicles, pedestrians, and road signs.
  - 근거: corpus: task, corpus: technique
- **C3.** The invention must incorporate collision avoidance and emergency handling systems to ensure passenger safety.
  - 근거: corpus: task, corpus: technique
- **C4.** The invention must integrate with existing transportation infrastructure, such as GPS and traffic management systems, to facilitate autonomous operation.
  - 근거: corpus: task, corpus: technique
- **C5.** The invention must provide real-time data processing and decision-making capabilities to adapt to changing conditions.
  - 근거: corpus: task, corpus: technique
- **C6.** The invention must include sensor integration and cross-validation to ensure the reliability and accuracy of autonomous vehicle systems.
  - 근거: corpus: technique, corpus: mismatch_with_web_evidence

## 분석 대상 특허의 범위
The scope of analysis for Autonomous Vehicle Technology includes patents that implement, improve, or provide enabling components or methods specific to autonomous vehicle systems. This encompasses technologies for vehicle perception, navigation, control, and communication that are integral to autonomous operation. Patents that merely use autonomous vehicle outputs or vocabulary for unrelated purposes are excluded.

## 범위 결정 (클러스터별 in/out)

- [OUT] **Cruise Control Systems** — Cruise control systems focus on maintaining a set speed and do not inherently enable autonomous navigation or decision-making.
- [IN] **Traffic Sign Recognition** — Traffic sign recognition is essential for autonomous vehicles to interpret and respond to road signs, a critical aspect of autonomous navigation.
- [IN] **Vehicle-to-Everything (V2X) Communication** — V2X communication is crucial for autonomous vehicles to interact with their environment, enhancing safety and navigation capabilities.
- [IN] **Collision Avoidance Systems** — Collision avoidance systems are fundamental to ensuring passenger safety in autonomous vehicles.
- [IN] **Sensor Cross-Validation** — Sensor cross-validation is important for ensuring the accuracy and reliability of data used in autonomous vehicle decision-making.
- [IN] **Obstacle Detection and Avoidance** — Obstacle detection and avoidance are core functions of autonomous vehicles, enabling them to navigate safely.
- [CONDITIONAL] **Lane Departure Warning Systems** — In if the system includes autonomous lane keeping or correction capabilities; out if it only provides warnings without autonomous intervention.
- [IN] **Autonomous Navigation and Path Planning** — Autonomous navigation and path planning are central to the operation of autonomous vehicles.
- [CONDITIONAL] **Adaptive Driving Assistance** — In if it includes autonomous decision-making and control; out if it only assists human drivers without autonomous capabilities.
- [IN] **Hazard Detection Systems** — Hazard detection is critical for autonomous vehicles to identify and respond to potential dangers.
- [IN] **Object Detection** — Object detection is a key component of the perception systems in autonomous vehicles.
- [IN] **Traffic Lane Detection** — Traffic lane detection is necessary for autonomous vehicles to navigate roads accurately.
- [IN] **Pedestrian Detection** — Pedestrian detection is essential for ensuring the safety of vulnerable road users in autonomous vehicle operation.
- [IN] **Autonomous Vehicle Control** — Autonomous vehicle control is a fundamental aspect of enabling vehicles to operate without human intervention.
- [IN] **Image Processing for Navigation** — Image processing is used in autonomous vehicles for interpreting visual data to aid navigation.
- [IN] **Sensor Integration for Autonomous Driving** — Sensor integration is crucial for combining data from multiple sources to enhance autonomous vehicle perception and decision-making.
- [IN] **Adaptive Motion Control** — Adaptive motion control is necessary for autonomous vehicles to adjust their movement based on environmental conditions.
- [CONDITIONAL] **Driving Assistance Systems** — In if the system includes autonomous capabilities; out if it only assists human drivers without autonomous functions.
- [IN] **Vehicle-to-Vehicle Communication** — Vehicle-to-vehicle communication is important for autonomous vehicles to coordinate with each other and improve safety.
- [IN] **Dynamic Vehicle Management** — Dynamic vehicle management involves real-time decision-making and control, which are essential for autonomous operation.
- [IN] **3D Point Cloud Generation** — 3D point cloud generation is used in autonomous vehicles for mapping and navigation.
- [IN] **Self-Driving Vehicle Allocation** — Self-driving vehicle allocation involves managing fleets of autonomous vehicles, which is part of the domain.
- [IN] **High Definition Map Updating** — High definition maps are used by autonomous vehicles for precise navigation and path planning.
- [IN] **Radar Systems for Vehicles** — Radar systems are used in autonomous vehicles for detecting objects and obstacles.
- [IN] **Remote Assistance for Autonomous Vehicles** — Remote assistance can be part of the support infrastructure for autonomous vehicles, aiding in navigation and control.
- [CONDITIONAL] **Driving Behavior Analysis** — In if it involves autonomous decision-making; out if it only analyzes human driving behavior without autonomous application.
- [IN] **Vehicle Data Acquisition** — Data acquisition is crucial for autonomous vehicles to gather information needed for navigation and decision-making.
- [IN] **Cloud-Based Mapping for Vehicles** — Cloud-based mapping supports autonomous vehicle navigation by providing up-to-date map data.
- [IN] **Indoor Self-Driving Vehicle Positioning** — Indoor positioning systems are used for autonomous navigation in environments like warehouses.
- [IN] **Smart Parking Systems** — Smart parking systems can be part of autonomous vehicle technology, enabling vehicles to park themselves.
- [IN] **Radar Technology for Vehicles** — Radar technology is used in autonomous vehicles for detecting and responding to environmental conditions.
- [CONDITIONAL] **Parking Assistance Technology** — In if it includes autonomous parking capabilities; out if it only assists human drivers without autonomous functions.
- [CONDITIONAL] **Electric Vehicle Technology** — In if it specifically integrates with autonomous systems to enhance autonomous operation; out if it only pertains to electric vehicle technology without autonomous application.
- [CONDITIONAL] **Network Synchronization Methods** — In if it supports autonomous vehicle communication by synchronizing data critical for autonomous operation; out if it pertains to general network synchronization without specific application to autonomous vehicles.
- [IN] **Automated Control Systems** — Automated control systems are integral to the operation of autonomous vehicles.
- [CONDITIONAL] **Transportation Systems** — In if it involves autonomous vehicle operation; out if it pertains to general transportation systems without autonomous application.
- [IN] **Obstacle Detection Systems** — Obstacle detection is a core function of autonomous vehicles, enabling safe navigation.
- [IN] **Parking Space Detection** — Parking space detection is used in autonomous vehicles to facilitate self-parking capabilities.
- [IN] **Vehicle Radar Technology** — Vehicle radar technology is used in autonomous vehicles for detecting objects and obstacles.
- [CONDITIONAL] **Driver Assistance Technologies** — In if it includes autonomous capabilities; out if it only assists human drivers without autonomous functions.
- [CONDITIONAL] **Vehicle Safety Features** — In if the safety features are specifically designed for autonomous vehicles; out if they are general vehicle safety features without autonomous application.
- [IN] **Distance Measurement Technologies** — Distance measurement is used in autonomous vehicles for navigation and collision avoidance.
- [CONDITIONAL] **Unmanned Aerial Vehicles** — In if the UAVs are used for autonomous navigation similar to ground vehicles; out if they pertain to aerial applications without relevance to ground vehicle autonomy.
- [IN] **Sensor Fusion** — Sensor fusion is used in autonomous vehicles to combine data from multiple sensors for improved perception and decision-making.
- [IN] **Path Planning** — Path planning is essential for autonomous vehicles to navigate routes safely and efficiently.
- [IN] **Environment Perception** — Environment perception is a critical component of autonomous vehicle systems, enabling them to understand and react to their surroundings.
- [IN] **Autonomous Navigation** — Autonomous navigation is the core function of autonomous vehicles, allowing them to operate without human intervention.

## 제외 기준 (E)

- **E1.** Patents that focus solely on driver assistance without autonomous capabilities are excluded.
  - 근거: corpus: task, corpus: technique
- **E2.** Patents related to vehicle components or systems that do not specifically enable or improve autonomous operation are excluded, unless they integrate with autonomous systems to enhance their functionality.
  - 근거: corpus: task, corpus: technique
- **E3.** Patents that involve automation for non-vehicle applications, such as home automation or industrial robots, are excluded.
  - 근거: corpus: boundary_case
- **E4.** Patents that pertain to unmanned aerial or marine vehicles without relevance to ground vehicle autonomy are excluded.
  - 근거: corpus: boundary_case

## 경계 판정 지침

- For patents related to 'Lane Departure Warning Systems', include them if they feature autonomous lane keeping or correction capabilities, otherwise exclude them if they only provide warnings.
- For 'Adaptive Driving Assistance', include if the system involves autonomous decision-making and control, otherwise exclude if it only assists human drivers.
- For 'Driving Assistance Systems', include if the system includes autonomous capabilities, otherwise exclude if it only assists human drivers.
- For 'Parking Assistance Technology', include if it features autonomous parking capabilities, otherwise exclude if it only assists human drivers.
- For 'Electric Vehicle Technology', include if it specifically integrates with autonomous systems to enhance autonomous operation, otherwise exclude if it only pertains to electric vehicle technology without autonomous application.
- For 'Network Synchronization Methods', include if it supports autonomous vehicle communication by synchronizing data critical for autonomous operation, otherwise exclude if it pertains to general network synchronization without specific application to autonomous vehicles.
- For 'Transportation Systems', include if it involves autonomous vehicle operation, otherwise exclude if it pertains to general transportation systems without autonomous application.
- For 'Driver Assistance Technologies', include if it includes autonomous capabilities, otherwise exclude if it only assists human drivers.
- For 'Vehicle Safety Features', include if the safety features are specifically designed for autonomous vehicles, otherwise exclude if they are general vehicle safety features without autonomous application.
- For 'Unmanned Aerial Vehicles', include if the UAVs are used for autonomous navigation similar to ground vehicles, otherwise exclude if they pertain to aerial applications without relevance to ground vehicle autonomy.
