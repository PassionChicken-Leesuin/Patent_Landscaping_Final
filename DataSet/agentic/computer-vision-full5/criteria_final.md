# 도메인 판단 기준서 — Computer Vision

## 도메인 정의
Computer vision is a field that involves the development of algorithms and systems that enable machines to interpret and understand visual information from the world, such as images and videos. This includes tasks such as object detection and recognition, image segmentation, 3D reconstruction from 2D images, motion tracking, spatial relationship interpretation, augmented reality, and structure from motion (SfM). The goal is to automate visual tasks that the human visual system can perform, using techniques like neural networks, feature extraction, and image processing.

## 도메인 판단 기준 (C)

- **C1.** The invention must involve the detection or recognition of objects within images or video streams.
  - 근거: corpus: object detection, corpus: image processing
- **C2.** The invention must include methods for interpreting spatial relationships or context within visual data.
  - 근거: corpus: spatial relationships, corpus: image segmentation
- **C3.** The invention must be capable of tracking movement or changes in visual scenes over time.
  - 근거: corpus: tracking systems, corpus: video analysis
- **C4.** The invention must involve segmenting images into meaningful regions or objects.
  - 근거: corpus: image segmentation, corpus: feature extraction
- **C5.** The invention must include techniques for reconstructing 3D models from 2D images.
  - 근거: corpus: 3D reconstruction, corpus: structure from motion
- **C6.** The invention must involve augmented reality applications that integrate real and virtual worlds in real-time.
  - 근거: corpus: augmented reality, corpus: 3D human–computer interaction
- **C7.** The invention must involve structure from motion (SfM) techniques for estimating 3D structures from 2D image sequences.
  - 근거: corpus: structure from motion, corpus: photogrammetric range imaging

## 분석 대상 특허의 범위
The scope of analysis for the computer vision domain includes patents that implement, improve, or provide enabling components or methods specific to computer vision tasks. This encompasses inventions related to object detection, image segmentation, 3D reconstruction, motion tracking, spatial interpretation, augmented reality, and structure from motion. Patents that merely use computer vision outputs or vocabulary for unrelated purposes are excluded.

## 범위 결정 (클러스터별 in/out)

- [IN] **image processing** — Image processing is integral to computer vision as it involves techniques for enhancing and analyzing images to extract meaningful information.
- [IN] **object detection** — Object detection is a core task in computer vision, involving the identification and localization of objects within images or videos.
- [CONDITIONAL] **neural networks** — Neural networks are in scope when they are specifically applied to computer vision tasks such as image recognition or segmentation.
- [IN] **video analysis** — Video analysis is in scope as it involves interpreting and extracting information from video data, a key aspect of computer vision.
- [CONDITIONAL] **biometric recognition** — Biometric recognition is in scope when it involves computer vision techniques for identifying individuals based on visual data.
- [CONDITIONAL] **medical imaging** — Medical imaging is in scope when it applies computer vision techniques for analyzing and interpreting medical images.
- [IN] **feature extraction** — Feature extraction is a fundamental process in computer vision for identifying and describing important image features.
- [CONDITIONAL] **deep learning** — Deep learning is in scope when it is used for computer vision tasks such as object detection or image classification.
- [IN] **image segmentation** — Image segmentation is a key computer vision task that involves dividing an image into meaningful parts.
- [IN] **tracking systems** — Tracking systems are in scope as they involve monitoring and analyzing movement within visual data.
- [CONDITIONAL] **autonomous vehicle systems** — Autonomous vehicle systems are in scope when they use computer vision for navigation and environment understanding.
- [IN] **3D reconstruction** — 3D reconstruction is a computer vision task that involves creating three-dimensional models from two-dimensional images.
- [IN] **pose estimation** — Pose estimation is in scope as it involves determining the position and orientation of objects within images.
- [IN] **image enhancement** — Image enhancement is in scope as it involves improving image quality for better analysis and interpretation in computer vision.
- [CONDITIONAL] **machine learning** — Machine learning is in scope when it is specifically applied to computer vision tasks.
- [CONDITIONAL] **robotics** — Robotics is in scope when it involves computer vision for tasks such as navigation, object manipulation, or environment interaction.
- [CONDITIONAL] **sensor data processing** — Sensor data processing is in scope when it involves integrating visual data for computer vision tasks.

## 제외 기준 (E)

- **E1.** Patents that focus solely on LED display control without performing computer vision tasks are excluded.
  - 근거: corpus: LED display control
- **E2.** Patents that involve image processing without specific applications in computer vision tasks such as object detection, segmentation, or 3D reconstruction are excluded.
  - 근거: corpus: image processing
- **E3.** Patents that focus on recognition tasks specific to non-general objects, such as tattoos, without broader computer vision applications are excluded.
  - 근거: corpus: recognition
- **E4.** Patents related to character recognition that do not encompass broader computer vision tasks are excluded.
  - 근거: corpus: character recognition
- **E5.** Patents focused on medical imaging without applying computer vision techniques such as segmentation or feature extraction are excluded.
  - 근거: corpus: medical imaging

## 경계 판정 지침

- For patents involving neural networks, assess whether the network is applied to a computer vision task such as image recognition or segmentation.
- For biometric recognition patents, determine if the recognition involves computer vision techniques for identifying individuals based on visual data.
- For medical imaging patents, verify if they apply computer vision techniques for analyzing and interpreting medical images.
- For autonomous vehicle systems, check if they use computer vision for navigation and environment understanding.
- For machine learning patents, ensure the learning is applied to computer vision tasks.
- For augmented reality patents, confirm they involve real-time integration of virtual and real-world elements using computer vision techniques.
- For structure from motion (SfM) patents, ensure they involve estimating 3D structures from 2D image sequences using computer vision methods.
- For LED display control patents, verify if they perform computer vision tasks beyond display control.
- For character recognition patents, ensure they encompass broader computer vision tasks beyond simple recognition.

## 사용자 결정이 필요한 범위 질문

- **Q2. Should autonomous vehicle systems be included when they use computer vision for navigation?**
  - 영향: 측정: 풀 표본 60건 중 6건(~10%)의 판정이 넓게/좁게에 따라 갈립니다. Including these systems recognizes the role of computer vision in enabling autonomous navigation, a major application area.
  - 선택지: Include autonomous vehicle systems when they use computer vision for navigation., Exclude autonomous vehicle systems unless they perform general computer vision tasks.
  - 현재 가정(미답변 시): Include autonomous vehicle systems when they use computer vision for navigation.
- **Q1. Does the domain include medical imaging when it applies computer vision techniques?**
  - 영향: 측정: 풀 표본 60건 중 5건(~8%)의 판정이 넓게/좁게에 따라 갈립니다. Including medical imaging expands the domain to cover a significant area of application where computer vision techniques are used.
  - 선택지: Include medical imaging when it applies computer vision techniques., Exclude medical imaging unless it is a general computer vision task.
  - 현재 가정(미답변 시): Include medical imaging when it applies computer vision techniques.
