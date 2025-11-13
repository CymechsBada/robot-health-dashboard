# 🤖 Robot Health Monitoring System

본 시스템은 반도체 제조 로봇의 **실시간 상태 모니터링**,  
**이력 관리**, **장기 트렌드 분석**, **이상 감지(Predictive Maintenance)** 를 수행하는  
웹 기반 헬스 모니터링 플랫폼입니다.

라즈베리파이에 설치하여 로봇 제어기의 데이터를 실시간 수집하고  
웹 UI로 시각화할 수 있습니다.

---

# 🚀 전체 설치 과정 한눈에 보기

라즈베리파이에서 아래 순서로 설치합니다:

0) 라즈베리파이 초기 준비  
1) 프로젝트 폴더 구성  
2) 데이터베이스 구성 (자동 생성)  
3) Python + 가상환경 + 라이브러리 설치  
4) Flask 서버 실행  

이 모든 과정은 `setup.sh` 실행으로 자동 처리할 수 있습니다.

---

# ⚡ 빠른 설치 (추천)

라즈베리파이에 프로젝트를 복사한 뒤 다음을 실행하세요:

```bash
cd health-monitoring
dos2unix setup.sh      # (Windows CRLF 방지)
chmod +x setup.sh
./setup.sh
