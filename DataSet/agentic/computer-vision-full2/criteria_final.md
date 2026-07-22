# 도메인 판단 기준서 — Computer Vision

## 도메인 정의
Computer vision is a field that involves the development of algorithms and systems to enable machines to interpret and understand visual information from the world, such as images and videos. This includes tasks such as object detection and recognition, image classification, 3D reconstruction from 2D images, tracking object movement across video frames, interpreting spatial relationships between objects in an image, image segmentation, and feature extraction.

## 도메인 판단 기준 (C)

- **C1.** The invention must involve the detection or recognition of objects within images or video streams.
  - 근거: corpus: Object detection is a computer technology related to computer vision and image processing that detects instances of semantic objects in digital images and videos.
- **C2.** The invention must describe a method for tracking the movement of objects across frames in a video.
  - 근거: corpus: Object detection is used in tasks such as image annotation, vehicle counting, and activity recognition.
- **C3.** The invention must involve interpreting the spatial relationships between objects in an image.
  - 근거: corpus: Computer vision involves acquiring, processing, analyzing, and understanding digital images to produce numerical or symbolic information.
- **C4.** The invention must involve reconstructing 3D models from 2D images.
  - 근거: corpus: Structure from motion (SfM) is a photogrammetric range imaging technique for estimating 3D structures from 2D image sequences.
- **C5.** The invention must involve classifying images into predefined categories based on their content.
  - 근거: corpus: ViTs have been applied in image recognition, image segmentation, weather prediction, and autonomous driving.
- **C6.** The invention must involve segmenting an image into meaningful parts or regions.
  - 근거: corpus: Image segmentation is a key computer vision task that involves partitioning an image into meaningful segments.
- **C7.** The invention must involve extracting features from images to describe important characteristics.
  - 근거: corpus: Feature extraction is a fundamental process in computer vision for identifying and describing important image characteristics.

## 분석 대상 특허의 범위
The scope of analysis for the computer vision domain includes patents that focus on the development of systems and algorithms for interpreting and understanding visual information from images and videos. This encompasses tasks such as object detection, image classification, 3D reconstruction, video analysis, image segmentation, and feature extraction. Patents that merely use computer vision outputs for other purposes, or focus on unrelated technologies like display control, are outside the scope.

## 범위 결정 (클러스터별 in/out)

- [IN] **Image Processing** — Image processing is a fundamental component of computer vision, as it involves techniques necessary for analyzing and interpreting visual data.
- [IN] **Object Detection** — Object detection is a core task in computer vision, involving the identification and localization of objects within images or videos.
- [IN] **Neural Networks** — Neural networks are widely used in computer vision for tasks such as image recognition and classification.
- [IN] **Deep Learning** — Deep learning techniques are integral to modern computer vision applications, enabling advanced image analysis and understanding.
- [IN] **Image Segmentation** — Image segmentation is a key computer vision task that involves partitioning an image into meaningful segments.
- [OUT] **Medical Imaging** — Medical imaging is ruled out as it focuses more on medical predictions rather than direct computer vision tasks, which is not aligned with the core computer vision tasks emphasized in the web evidence.
- [IN] **Facial Recognition** — Facial recognition is a specific application of computer vision involving the identification of individuals based on facial features.
- [IN] **Video Analysis** — Video analysis involves interpreting and understanding video content, a direct application of computer vision.
- [IN] **Feature Extraction** — Feature extraction is a fundamental process in computer vision for identifying and describing important image characteristics.
- [IN] **Optical Character Recognition** — Optical character recognition involves the conversion of images of text into machine-encoded text, a specific application of computer vision.

## 제외 기준 (E)

- **E1.** Patents focusing on LED display control are excluded as they pertain to display technology rather than image analysis or recognition.
  - 근거: corpus: Patents focusing on LED display control, such as 'A kind of LED display control method and control system', are more about display technology than image analysis or recognition.
- **E2.** Patents involving input devices, like hand-written character input devices, are excluded as they focus on input mechanisms rather than image analysis tasks like OCR.
  - 근거: corpus: Patents involving input devices, like 'Hand-written character input device', focus more on input mechanisms than computer vision itself.
- **E3.** Patents related to machine vision in factory automation are excluded as they focus on systems engineering rather than the core computer vision tasks of interpreting and understanding visual information.
  - 근거: corpus: Machine vision refers to a systems engineering discipline, especially in the context of factory automation.

## 경계 판정 지침

- Patents like 'Method and apparatus for processing image' should be included if they specify applications in computer vision tasks such as object detection or image classification.
- Patents related to specific recognition tasks, such as 'Detection and tracking system using tattoos', should be included if they involve core computer vision tasks like object detection or tracking, otherwise they should be excluded if they do not contribute to broader computer vision applications.
