# 도메인 판단 기준서 — Computer Vision

## 도메인 정의
Computer vision is a field of artificial intelligence that enables machines to interpret and understand visual information from the world, such as images and videos. It involves tasks such as object detection and recognition, image segmentation, tracking of movement and changes in visual scenes, 3D reconstruction, and image enhancement or restoration. These tasks are achieved through the use of algorithms and models that process and analyze visual data to extract meaningful information, often mimicking the capabilities of the human visual system.

## 도메인 판단 기준 (C)

- **C1.** The invention must involve the detection or recognition of objects within images or video streams.
  - 근거: corpus: task, corpus: definition
- **C2.** The invention must be capable of interpreting spatial relationships and context within visual data.
  - 근거: corpus: definition, corpus: task
- **C3.** The invention must involve tracking movement and changes in visual scenes over time.
  - 근거: corpus: task, corpus: definition
- **C4.** The invention must perform image segmentation to divide images into meaningful parts or regions for further analysis.
  - 근거: corpus: task, corpus: definition
- **C5.** The invention must enhance or restore images to improve visual quality or extract more information.
  - 근거: corpus: task, corpus: definition
- **C6.** The invention must involve 3D reconstruction or modeling from 2D image sequences.
  - 근거: corpus: definition, corpus: task

## 분석 대상 특허의 범위
The scope of analysis for the computer vision domain includes patents that perform tasks related to the interpretation and understanding of visual data, such as object detection, image segmentation, tracking, 3D reconstruction, and image enhancement. Patents that merely use visual data for unrelated purposes or focus on non-visual data processing are outside the scope.

## 범위 결정 (클러스터별 in/out)

- [IN] **image processing methods** — These methods are in scope as they often involve tasks like object detection, image segmentation, and enhancement, which are core to computer vision.
- [IN] **object detection** — Object detection is a fundamental task in computer vision, involving the identification and localization of objects within images or videos.
- [CONDITIONAL] **neural networks** — Neural networks are in scope when they are applied to computer vision tasks such as object detection, image segmentation, or 3D reconstruction. The decisive test is whether the neural network is specifically used for visual data interpretation.
- [IN] **biometric recognition** — Biometric recognition involves the detection and analysis of visual features, which aligns with computer vision tasks.
- [IN] **video analysis** — Video analysis is in scope as it involves tracking and interpreting changes in visual scenes over time.
- [CONDITIONAL] **medical imaging** — Medical imaging is in scope when it involves computer vision tasks like image segmentation or enhancement. The decisive test is whether the imaging method performs a computer vision task.
- [IN] **feature extraction** — Feature extraction is a key process in computer vision for analyzing and interpreting visual data.
- [CONDITIONAL] **deep learning applications** — Deep learning applications are in scope when they are used for computer vision tasks. The decisive test is whether the application involves visual data interpretation.
- [IN] **image segmentation** — Image segmentation is a core computer vision task, dividing images into meaningful parts for analysis.
- [IN] **tracking systems** — Tracking systems are in scope as they involve monitoring movement and changes in visual scenes.
- [IN] **3D reconstruction and modeling** — 3D reconstruction is a computer vision task that involves creating 3D models from 2D images.
- [IN] **facial recognition and analysis** — Facial recognition involves detecting and analyzing visual features, aligning with computer vision tasks.
- [CONDITIONAL] **environmental monitoring using images** — Environmental monitoring is in scope when it involves computer vision tasks like object detection or 3D modeling. The decisive test is whether the monitoring uses visual data for interpretation.
- [IN] **pose estimation** — Pose estimation involves interpreting spatial relationships in visual data, a core computer vision task.
- [IN] **image quality evaluation** — Image quality evaluation and enhancement are part of image processing tasks in computer vision.
- [IN] **real-time video analysis** — Real-time video analysis involves tracking and interpreting changes in visual scenes, a computer vision task.
- [CONDITIONAL] **autonomous vehicle driving** — Autonomous driving is in scope when it involves computer vision tasks like object detection or tracking. The decisive test is whether the driving system uses visual data for navigation.
- [IN] **optical character recognition** — Optical character recognition involves detecting and interpreting text in images, a computer vision task.
- [IN] **image depth estimation** — Image depth estimation involves interpreting spatial relationships in visual data, a computer vision task.
- [CONDITIONAL] **vision sensing devices** — Vision sensing devices are in scope when they are used for computer vision tasks. The decisive test is whether the device is designed for visual data interpretation.
- [IN] **pedestrian detection** — Pedestrian detection is a specific application of object detection, a core computer vision task.
- [IN] **human body behavior recognition** — Human body behavior recognition involves interpreting visual data to understand actions, a computer vision task.
- [IN] **defect detection in images** — Defect detection involves analyzing images to identify anomalies, a computer vision task.
- [CONDITIONAL] **video signal processing** — Video signal processing is in scope when it involves computer vision tasks like tracking or segmentation. The decisive test is whether the processing is for visual data interpretation.
- [CONDITIONAL] **neural network applications in imaging** — Neural network applications are in scope when used for computer vision tasks. The decisive test is whether the application involves visual data interpretation.

## 제외 기준 (E)

- **E1.** Patents that focus on display technology without performing computer vision tasks are excluded.
  - 근거: corpus: confusable
- **E2.** Patents that involve image processing without specific applications in computer vision tasks are excluded.
  - 근거: corpus: boundary_case
- **E3.** Patents focused on audio or text processing rather than visual data interpretation are excluded.
  - 근거: corpus: boundary_case
- **E4.** Patents involving optimization problems or hardware implementation not related to computer vision tasks are excluded.
  - 근거: corpus: boundary_case
- **E5.** Patents focused on non-visual data processing, such as biological signals or wireless technology, are excluded.
  - 근거: corpus: boundary_case

## 경계 판정 지침

- LED display control methods are out of scope unless they perform computer vision tasks like image analysis.
- Methods for processing images are in scope only if they involve specific computer vision tasks like object detection or segmentation.
- Recognition systems for tattoos are in scope if they involve computer vision tasks like feature extraction or pattern recognition.
- Character input devices are out of scope unless they perform computer vision tasks like optical character recognition.
- Medical imaging systems are in scope if they perform computer vision tasks like image segmentation or enhancement.
- Environmental monitoring methods are in scope if they involve computer vision tasks like object detection or 3D modeling.
- Systems focused on audio processing are out of scope unless they involve visual data interpretation.
- Methods involving signal processing related to biological signals are out of scope unless they involve visual data interpretation.
- Systems focused on text processing are out of scope unless they involve visual data interpretation.
- Methods involving optimization problems are out of scope unless they are directly related to computer vision tasks.
