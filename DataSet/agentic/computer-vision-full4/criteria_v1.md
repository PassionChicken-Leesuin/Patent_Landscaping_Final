# 도메인 판단 기준서 — Computer Vision

## 도메인 정의
Computer vision is a field focused on enabling machines to interpret and understand visual information from the world, such as images and videos, by performing tasks like object detection, scene segmentation, feature extraction, and 3D reconstruction. It involves the development of algorithms and systems that can process, analyze, and derive meaningful insights from visual data, often mimicking human visual perception capabilities.

## 도메인 판단 기준 (C)

- **C1.** The invention must involve the detection or identification of objects within images or video streams.
  - 근거: corpus: task, corpus: definition
- **C2.** The invention must include methods for interpreting spatial relationships or context within visual data.
  - 근거: corpus: definition, corpus: task
- **C3.** The invention must involve tracking movement or changes in visual scenes over time.
  - 근거: corpus: task, corpus: definition
- **C4.** The invention must involve reconstructing 3D models from 2D images or video.
  - 근거: corpus: definition, corpus: task
- **C5.** The invention must involve classifying or categorizing visual data into predefined categories.
  - 근거: corpus: definition, corpus: task
- **C6.** The invention must involve feature extraction from images or videos, such as detecting edges, corners, or other significant points.
  - 근거: corpus: technique, corpus: definition

## 분석 대상 특허의 범위
The scope of analysis for the computer vision domain includes patents that implement, improve, or provide enabling components or methods specific to computer vision tasks such as object detection, scene segmentation, feature extraction, and 3D reconstruction. It also includes specific applications of these technologies, provided they are integral to the computer vision process. Patents that merely use computer vision outputs or vocabulary for unrelated purposes are excluded.

## 범위 결정 (클러스터별 in/out)

- [CONDITIONAL] **Image Processing** — In-scope if the processing is specifically for computer vision tasks like object detection or feature extraction; out if it is generic image enhancement or unrelated processing.
- [IN] **Object Detection** — Object detection is a core task of computer vision, involving identifying and locating objects within images or videos.
- [CONDITIONAL] **Neural Networks** — In-scope if the neural networks are specifically designed for computer vision tasks; out if they are for general-purpose applications.
- [IN] **Video Analysis** — Video analysis is in-scope as it involves interpreting and understanding visual information over time, a key aspect of computer vision.
- [CONDITIONAL] **Biometric Recognition** — In-scope if it involves computer vision techniques for recognizing biometric features; out if it relies solely on non-visual data.
- [CONDITIONAL] **Medical Imaging** — In-scope if it uses computer vision techniques for analyzing medical images; out if it focuses solely on imaging technology without computer vision analysis.
- [IN] **Feature Extraction** — Feature extraction is a fundamental computer vision task, involving identifying significant points or patterns in images.
- [IN] **Scene Segmentation** — Scene segmentation is a core computer vision task, involving dividing an image into meaningful segments.
- [CONDITIONAL] **Deep Learning** — In-scope if deep learning is applied to computer vision tasks; out if used for non-vision-related purposes.
- [CONDITIONAL] **Character Recognition** — In-scope if it involves computer vision techniques for recognizing characters; out if it is purely about input device technology.
- [IN] **3D Reconstruction** — 3D reconstruction from 2D images is a key computer vision task, involving creating 3D models from visual data.
- [IN] **Facial Recognition** — Facial recognition is a specific application of computer vision, involving identifying or verifying faces in images or videos.
- [CONDITIONAL] **Autonomous Vehicle Systems** — In-scope if the systems use computer vision for navigation or object detection; out if they rely on non-vision sensors.
- [OUT] **Image Enhancement** — Image enhancement is out of scope unless it specifically supports a computer vision task.
- [IN] **Multi-object Tracking** — Multi-object tracking is a computer vision task involving tracking multiple objects over time in video data.
- [IN] **Pose Estimation** — Pose estimation is a computer vision task involving determining the position and orientation of objects or people.
- [OUT] **Image Quality Evaluation** — Image quality evaluation is out of scope unless it directly supports a computer vision task.
- [CONDITIONAL] **Environmental Monitoring using Images** — In-scope if it involves computer vision techniques for analyzing environmental data; out if it is purely about data collection.
- [OUT] **Real-time Image Capture** — Real-time image capture is out of scope unless it specifically supports a computer vision task.
- [CONDITIONAL] **Optical Character Recognition** — In-scope if it involves computer vision techniques; out if it is purely about text input technology.

## 제외 기준 (E)

- **E1.** Patents that focus on image processing without specific applications in computer vision tasks are excluded.
  - 근거: corpus: boundary_case, patent-pool: suspected_boundary_cases
- **E2.** Patents related to display technology, such as LED display control, are excluded unless they specifically involve computer vision tasks.
  - 근거: patent-pool: suspected_boundary_cases
- **E3.** Patents that involve character recognition purely as input devices without computer vision techniques are excluded.
  - 근거: patent-pool: suspected_boundary_cases
- **E4.** Medical imaging patents that do not apply computer vision techniques for analysis are excluded.
  - 근거: patent-pool: suspected_boundary_cases

## 경계 판정 지침

- For patents like 'Method and apparatus for processing image', determine if the processing is specifically for computer vision tasks; if not, exclude.
- For 'Detection and tracking system using tattoos', assess if the system uses computer vision techniques for broader applications; if not, exclude.
- For 'System and method for cardioembolic stroke risk prediction based on medical images', include only if computer vision techniques are used for image analysis.
