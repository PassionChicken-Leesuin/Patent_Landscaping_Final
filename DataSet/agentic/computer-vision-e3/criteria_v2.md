# 도메인 판단 기준서 — Computer Vision

## 도메인 정의
Computer vision is a field focused on enabling machines to interpret and understand visual information from the world, primarily through the processing and analysis of digital images and video. This involves tasks such as object detection, recognition, and tracking, depth estimation, 3D modeling, and feature detection and extraction, often leveraging machine learning techniques to improve accuracy and adaptability. The goal is to automate visual tasks that the human visual system can perform, such as identifying objects, understanding scenes, and extracting meaningful information from visual data.

## 도메인 판단 기준 (C)

- **C1.** The invention must involve the detection, recognition, or tracking of objects within digital images or video streams.
  - 근거: corpus: Object detection is a computer technology related to computer vision and image processing that detects instances of semantic objects in digital images and videos., corpus: Object detection has applications in image retrieval and video surveillance.
- **C2.** The invention must include techniques for interpreting and analyzing visual data to extract meaningful information, such as depth estimation or scene understanding.
  - 근거: corpus: Computer vision involves acquiring, processing, analyzing, and understanding digital images to produce numerical or symbolic information., corpus: Stereo vision is important in robotics for extracting 3D object positions.
- **C3.** The invention must perform image processing tasks such as filtering, enhancement, or transformation as part of a larger computer vision system.
  - 근거: corpus: Image processing is a related field that involves determining information from an image through computation., corpus: Graph cut optimization is used to solve low-level computer vision problems like image smoothing and segmentation.
- **C4.** The invention must utilize machine learning techniques for visual recognition tasks, which can be inferred from the presence of terms like 'neural network' or 'deep learning' in the title or abstract.
  - 근거: corpus: Neural network approaches for object detection include R-CNN, YOLO, and SSD., corpus: Unsupervised domain adaptation approaches address challenges caused by domain gaps in object detection.
- **C5.** The invention must involve the generation or use of 3D models from 2D images, such as through Structure from Motion or stereo vision techniques.
  - 근거: corpus: Structure from motion (SfM) is a photogrammetric range imaging technique for estimating 3D structures from 2D image sequences., corpus: Computer stereo vision extracts 3D information from digital images using two vantage points.
- **C6.** The invention must involve feature detection and extraction from images, which is fundamental to computer vision tasks.
  - 근거: corpus: Feature detection is a low-level image processing operation in computer vision., corpus: Features in computer vision can be points, edges, or objects in an image.

## 분석 대상 특허의 범위
The scope of analysis for the computer vision domain includes patents that focus on enabling machines to interpret and understand visual data through techniques such as object detection, recognition, tracking, depth estimation, 3D modeling, and feature detection and extraction. This includes the use of machine learning to enhance these tasks. Patents that merely use visual data for unrelated purposes or focus on non-visual tasks are outside the scope.

## 범위 결정 (클러스터별 in/out)

- [IN] **Image processing methods and enhancement** — These methods are integral to computer vision as they involve processing visual data to extract meaningful information.
- [IN] **Neural network applications and machine learning** — Neural networks are crucial for improving the accuracy and adaptability of computer vision tasks.
- [IN] **Object detection and recognition** — Object detection and recognition are core tasks of computer vision.
- [OUT] **Signal processing techniques** — While related, signal processing alone does not necessarily involve interpreting visual data in the context of computer vision.
- [OUT] **Graph generation methods** — Graph generation is not specific to computer vision unless it directly involves visual data interpretation.
- [IN] **Sports video analysis** — Analyzing video for object detection and tracking falls within the scope of computer vision.
- [IN] **Air quality estimation from images** — This involves interpreting visual data to extract meaningful information, aligning with computer vision tasks.
- [IN] **Depth estimation from images** — Depth estimation is a key task in computer vision for understanding 3D structures.
- [IN] **3D modeling and optimization** — 3D modeling from visual data is a fundamental aspect of computer vision.
- [IN] **Image registration and tracking** — Tracking and registering images are essential tasks in computer vision.
- [IN] **Microscopic imaging methods** — If these methods involve computer vision tasks like object detection or 3D modeling, they are within the scope.
- [OUT] **Network and data management** — These tasks do not involve the interpretation of visual data.
- [OUT] **User authentication and security** — Unless specifically involving visual recognition, these tasks are outside the scope.
- [OUT] **Predictive modeling and customer behavior analysis** — These tasks do not involve interpreting visual data.
- [IN] **Vehicle control and road condition detection** — These tasks often involve computer vision for interpreting visual data from the environment.

## 제외 기준 (E)

- **E1.** Patents that focus solely on image processing without the context of interpreting or understanding visual data do not belong to the computer vision domain.
  - 근거: corpus: Image processing is a related field that involves determining information from an image through computation.
- **E2.** Patents that use visual data for non-interpretative purposes, such as simple display or storage, are excluded from the computer vision domain.
  - 근거: corpus: Computer graphics involves algorithms for generating visual images and integrating visual information from the real world.
- **E3.** Patents related to basic image storage or display technologies without any interpretation or analysis of the visual data are excluded from the computer vision domain.
  - 근거: corpus: Computer graphics involves algorithms for generating visual images and integrating visual information from the real world.

## 경계 판정 지침

- For patents like 'Air quality estimation from images', if the method involves interpreting visual data to derive information, it is within scope.
- For 'Sports video analysis', if the analysis involves object detection or tracking, it is within scope.
- For 'Graph generation methods', unless the graph generation directly involves interpreting visual data, it is out of scope.
- For 'Microscopic imaging methods', if they involve tasks like object detection or 3D modeling, they are within scope.
