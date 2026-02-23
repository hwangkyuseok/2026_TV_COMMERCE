# Project: Smart TV Commerce Platform (Prototype Phase)

## 1. Project Overview
- **Objective:** 셋톱박스용 개인화 방송 추천 및 객체 인식 기반 쇼핑 서비스의 초기 프로토타입 구축.
- **Current Phase:** 백엔드 세부 로직(DB 연동, YOLO 추론)은 제외하고, **Mock Data 기반의 FastAPI 백엔드**와 **Next.js 프론트엔드**가 통신하며 화면을 그리는 것까지 단번에 구현한다.
- **Tech Stack:** Next.js (App Router, Tailwind CSS), FastAPI (Pydantic), Docker Compose.

## 2. Core Engineering Rules
- **Remote Control First (가장 중요):** TV 환경이므로 마우스 클릭을 배제한다. 리모컨 방향키(`ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`)와 `Enter` 키로 화면 내 모든 컴포넌트(메뉴, 캐러셀, 바둑판 그리드, 모달창) 간에 포커스(Focus)가 이동해야 한다.
- **Focus Trap:** 팝업(모달) 등장 시, 포커스가 절대 모달 밖으로 나가지 않도록 완벽히 가둔다.
- **Mock-Driven API:** FastAPI는 현재 복잡한 로직 없이, 제공된 `mock_data.json`을 읽어 그대로 반환하는 엔드포인트(`/api/v1/data`)만 제공한다. 프론트엔드는 화면 로드 시 이 API를 호출하여 데이터를 렌더링한다.
- **결제 동선 분기:** 상품 가격이 20만 원 이상이면 '상담원 연결(전화번호 입력)' 모달을, 미만이면 '바로 구매' 모달을 띄운다.