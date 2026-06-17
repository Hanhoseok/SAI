# SAI

> 2021 POSCO AI Challenge에서 개발한 **수어 번역기 프로토타입**입니다.

SAI는 웹캠으로 입력된 수어 동작을 인식해 텍스트로 변환하고, 필요하면 다시 **음성** 또는 **수어 영상** 형태로 출력하는 PyQt 기반 데스크톱 서비스입니다. 한국수어(KSL)와 미국수어(ASL)를 모두 다루며, 한국어/영어 텍스트 및 음성 흐름을 함께 실험했습니다.

---

## What It Does

- 웹캠 기반 수어 인식
- 한국수어(KSL) / 미국수어(ASL) 분류
- 한국어 / 영어 텍스트 변환
- 마이크 입력 기반 Speech-to-Text
- Papago 기반 한영 번역
- gTTS 기반 Text-to-Speech 출력
- 사전 저장된 수어 영상 재생

---

## How It Works

1. 사용자가 웹캠, 텍스트, 또는 마이크 입력을 선택합니다.
2. 웹캠 입력의 경우 MediaPipe Holistic으로 손/상체 랜드마크를 추출합니다.
3. 랜드마크를 시퀀스 벡터로 가공한 뒤, 30프레임 단위 입력으로 LSTM 모델에 전달합니다.
4. 모델이 수어 단어를 분류하면 결과를 텍스트로 출력합니다.
5. 필요하면 Papago로 번역하고, gTTS로 음성 출력하거나 대응 수어 영상을 이어서 재생합니다.

---

## Tech Stack

- **Python**
- **PyQt5** — 데스크톱 GUI
- **OpenCV** — 카메라 입력 및 영상 처리
- **MediaPipe** — 손/포즈 랜드마크 추출
- **TensorFlow / Keras** — LSTM 기반 수어 분류 모델
- **SpeechRecognition** — 음성 입력 인식
- **gTTS / pyglet** — 음성 합성 및 재생
- **Papago API** — 한영 번역

---

## Current Vocabulary Scope

현재 공개 저장소 기준 모델은 **고정된 핵심 표현 집합**을 대상으로 동작합니다.

### KSL labels
- 딸
- 잃어버리다
- 안내소
- 어디
- 도와주세요
- 배
- 아프다
- 화장실

### ASL labels
- daughter
- lost
- information_desk
- where
- help
- stomach
- sick
- toilet

---

## Key Files

- `main.py` — PyQt UI, 입력/출력 제어, 수어 인식 파이프라인 메인 로직
- `google_speech.py` — 마이크 입력 음성 인식
- `papago.py` — 한영 번역 요청
- `Text_To_Speech.py` — 텍스트 음성 변환
- `video_merge_cv.py` — 단어별 수어 영상 재생
- `KSL(Split)_LSTM.h5` / `ASL(Split)_LSTM.h5` — 수어 분류 모델

---

## Run

```bash
pip install -r requirements.txt
python main.py
```

> 실행 시 카메라, 모델 파일, 그리고 프로젝트에서 사용하는 이미지/비디오 자산이 필요합니다.

---

## Limitations

- 현재 형태는 **자유 문장 번역기**가 아니라 **고정 어휘 분류 기반 프로토타입**입니다.
- 단어 수가 제한적이어서 실제 대화 전반을 처리하기에는 범위가 좁습니다.
- 데스크톱 환경과 로컬 자산 파일에 의존합니다.

---

## About

수어 사용자와 비수어 사용자 사이의 의사소통 장벽을 낮추는 보조 도구를 목표로 한 프로젝트입니다.
