# Preto-2

Docker 기반 Jupyter Notebook + Streamlit 로컬 개발환경

## 사전 준비

### Docker Desktop 설치

개발환경을 실행하려면 **Docker Desktop**이 필요합니다.

| 운영체제 | 다운로드 링크 |
|---------|-------------|
| Mac | https://docs.docker.com/desktop/install/mac-install/ |
| Windows | https://docs.docker.com/desktop/install/windows-install/ |

설치 후 Docker Desktop을 실행하고, 화면 하단에 "Docker Desktop is running"이 표시될 때까지 기다려주세요.

---

## 빠른 시작

### Mac 사용자

**터미널**을 열고 프로젝트 폴더로 이동한 후 아래 명령어를 순서대로 실행하세요.

```bash
# 1. Docker 이미지 빌드 (최초 1회만 실행)
make docker-build

# 2. 개발환경 시작
make docker-run
```

### Windows 사용자

**PowerShell** 또는 **명령 프롬프트(CMD)**를 열고 프로젝트 폴더로 이동한 후 아래 명령어를 순서대로 실행하세요.

```powershell
# 1. Docker 이미지 빌드 (최초 1회만 실행)
docker build -t preto-2 .

# 2. 개발환경 시작
docker run -d --name preto-2-container -p 8501:8501 -p 8888:8888 -v ${PWD}/src:/app/src -v ${PWD}/notebooks:/app/notebooks -e ENVIRONMENT=dev preto-2
```

> **CMD 사용자**: `${PWD}` 대신 `%cd%`를 사용하세요.
> ```cmd
> docker run -d --name preto-2-container -p 8501:8501 -p 8888:8888 -v %cd%/src:/app/src -v %cd%/notebooks:/app/notebooks -e ENVIRONMENT=dev preto-2
> ```

---

## 접속하기

개발환경이 실행되면 웹 브라우저에서 아래 주소로 접속하세요.

| 서비스 | 주소 | 설명 |
|-------|------|------|
| **Streamlit** | http://localhost:8501 | 대시보드 앱 |
| **Jupyter Notebook** | http://localhost:8888 | 데이터 분석 노트북 |

---

## 개발환경 종료

### Mac 사용자

```bash
make docker-stop
```

### Windows 사용자

```powershell
docker stop preto-2-container
docker rm preto-2-container
```

---

## 로컬 실행 (Docker 없이)

Docker 없이 로컬에서 직접 실행할 수도 있습니다.

### 사전 준비

Python 3.12 이상이 설치되어 있어야 합니다.

```bash
# 패키지 설치 (최초 1회)
make install
# 또는
pip install -r requirements.txt
```

### Mac 사용자

```bash
# Jupyter만 실행
make jupyter

# Jupyter + Streamlit 동시 실행
make dev
```

### Windows 사용자

**PowerShell:**
```powershell
# Jupyter만 실행
$env:PYTHONPATH="$PWD\src"; jupyter notebook --notebook-dir=notebooks

# Streamlit만 실행
streamlit run src/app.py
```

**CMD:**
```cmd
# Jupyter만 실행
set PYTHONPATH=%cd%\src && jupyter notebook --notebook-dir=notebooks

# Streamlit만 실행
streamlit run src/app.py
```

---

## Jupyter에서 src 모듈 사용하기

`make jupyter` 또는 위의 PYTHONPATH 설정으로 Jupyter를 실행하면, 노트북에서 `src/` 하위 모듈을 바로 import할 수 있습니다.

```python
# src/app.py의 함수 import
from app import foo

# src/services/data.py가 있다면
from services.data import load_data
```

> **참고**: `src/` 하위에 패키지를 만들려면 `__init__.py` 파일이 필요합니다.

---

## 자주 사용하는 명령어

### Mac (Makefile)

| 명령어 | 설명 |
|-------|------|
| `make install` | Python 패키지 설치 |
| `make jupyter` | 로컬 Jupyter 실행 |
| `make dev` | 로컬 Jupyter + Streamlit 실행 |
| `make start` | 로컬 Streamlit만 실행 |
| `make docker-build` | Docker 이미지 빌드 |
| `make docker-run` | Docker 개발 모드로 실행 |
| `make docker-run-prod` | Docker 프로덕션 모드로 실행 |
| `make docker-stop` | Docker 컨테이너 종료 |
| `make docker-logs` | Docker 로그 확인 |
| `make docker-shell` | Docker 컨테이너 내부 접속 |

### Windows (Docker 명령어)

| 작업 | 명령어 |
|-----|-------|
| 이미지 빌드 | `docker build -t preto-2 .` |
| 개발 모드 실행 | `docker run -d --name preto-2-container -p 8501:8501 -p 8888:8888 -v ${PWD}/src:/app/src -v ${PWD}/notebooks:/app/notebooks -e ENVIRONMENT=dev preto-2` |
| 프로덕션 모드 실행 | `docker run -d --name preto-2-container -p 8501:8501 -e ENVIRONMENT=prod -e STREAMLIT_DEV_MODE=false preto-2` |
| 컨테이너 종료 | `docker stop preto-2-container && docker rm preto-2-container` |
| 로그 확인 | `docker logs -f preto-2-container` |
| 컨테이너 내부 접속 | `docker exec -it preto-2-container /bin/bash` |

---

## 개발 모드 vs 프로덕션 모드

| 항목 | 개발 모드 | 프로덕션 모드 |
|-----|----------|-------------|
| Jupyter Notebook | 사용 가능 (8888) | 비활성화 |
| Streamlit | 사용 가능 (8501) | 사용 가능 (8501) |
| 코드 자동 반영 | O (볼륨 마운트) | X |
| 용도 | 개발/테스트 | 배포 |

---

## 문제 해결

### "Docker Desktop is not running" 오류

Docker Desktop 앱을 실행해주세요. 시스템 트레이(Mac: 메뉴바, Windows: 작업표시줄)에서 Docker 아이콘을 확인하세요.

### "port is already allocated" 오류

이미 실행 중인 컨테이너가 있습니다. 먼저 종료하세요.

**Mac:**
```bash
make docker-stop
```

**Windows:**
```powershell
docker stop preto-2-container
docker rm preto-2-container
```

### "name is already in use" 오류

같은 이름의 컨테이너가 존재합니다. 삭제 후 다시 실행하세요.

**Mac:**
```bash
make docker-stop
make docker-run
```

**Windows:**
```powershell
docker rm preto-2-container
# 그 후 docker run 명령어 다시 실행
```

### 코드 수정이 반영되지 않을 때

Streamlit 페이지에서 브라우저를 새로고침(F5)하거나, 우측 상단의 "Rerun" 버튼을 클릭하세요.

### Windows에서 볼륨 마운트가 안 될 때

Docker Desktop > Settings > Resources > File Sharing에서 프로젝트 폴더가 포함된 드라이브가 공유되어 있는지 확인하세요.

---

## 프로젝트 구조

```
preto-2/
├── Dockerfile              # Docker 이미지 설정
├── Makefile                # Mac용 명령어 단축
├── requirements.txt        # Python 패키지 목록
├── jupyter_notebook_config.py  # Jupyter 설정
├── .streamlit/
│   └── config.toml         # Streamlit 설정
├── scripts/
│   ├── start.sh            # 시작 스크립트 (분기)
│   ├── start-dev.sh        # 개발 모드 스크립트
│   └── start-prod.sh       # 프로덕션 모드 스크립트
├── src/
│   └── app.py              # Streamlit 앱 코드
└── notebooks/
    └── (노트북 파일들)       # Jupyter 노트북 저장 위치
```
