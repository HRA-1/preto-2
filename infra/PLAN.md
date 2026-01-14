# preto-2 인프라 구현 계획

## 개요

HRA-1/preto-1의 인프라 구조를 참고하여 preto-2에 Terraform 인프라와 GitHub Actions CI/CD를 구현합니다.

### 구성 선택

- **AWS 환경**: preto-1과 동일한 계정/VPC 사용
- **S3 Backend**: 기존 `preto-terraform-state` 버킷 공유
- **환경 분리**: prod 환경만 구성

---

## 1. 디렉토리 구조

```
preto-2/
├── infra/
│   ├── PLAN.md              # 이 파일
│   └── terraform/
│       ├── README.md
│       ├── modules/
│       │   ├── ecr/         # ECR 리포지토리
│       │   ├── ecs/         # ECS Cluster, Service, Task
│       │   ├── iam/         # IAM Roles
│       │   └── network/     # ALB, Target Group
│       └── environments/
│           └── prod/
│               ├── backend.tf
│               ├── main.tf
│               ├── variables.tf
│               └── outputs.tf
│
└── .github/
    └── workflows/
        ├── README.md
        ├── terraform-plan.yml
        ├── terraform-apply.yml
        └── docker-build.yml
```

---

## 2. Terraform 모듈

| 모듈 | 역할 | 리소스 |
|------|------|--------|
| `ecr` | Docker 이미지 저장소 | ECR Repository, Lifecycle Policy |
| `iam` | ECS 실행 권한 | Task Execution Role, Task Role |
| `ecs` | 컨테이너 오케스트레이션 | Cluster, Task Definition, Service, CloudWatch Logs |
| `network` | 네트워크 및 로드밸런싱 | ALB, Target Group, Listener |

---

## 3. GitHub Actions 워크플로우

| 워크플로우 | 트리거 | 역할 |
|-----------|--------|------|
| `terraform-plan.yml` | PR 생성 (infra 변경) | Plan 결과를 PR 코멘트로 표시 |
| `terraform-apply.yml` | PR merge (infra 변경) | 인프라 자동 적용 |
| `docker-build.yml` | PR merge (app 변경) | Docker 빌드 → ECR 푸시 → ECS 배포 |

### OIDC 인증

preto-1에서 설정한 `GitHubActionsRole` IAM Role을 재사용합니다.

---

## 4. 사전 준비 작업 (수동)

### 4.1 AWS IAM Trust Policy 업데이트

기존 `GitHubActionsRole`의 Trust Policy에 preto-2 리포지토리를 추가해야 합니다:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": [
            "repo:HRA-1/preto-1:*",
            "repo:HRA-1/preto-2:*"
          ]
        }
      }
    }
  ]
}
```

### 4.2 GitHub Repository Secret 설정

Repository Settings → Secrets and variables → Actions에서:

- `AWS_ROLE_ARN`: `arn:aws:iam::<ACCOUNT_ID>:role/GitHubActionsRole`

### 4.3 GitHub Environment 설정 (선택)

Settings → Environments에서 `prod` Environment 생성 및 Protection Rules 설정

---

## 5. 배포 순서

### 5.1 최초 배포

```bash
# 1. Terraform 초기화 및 검증
cd infra/terraform/environments/prod
terraform init
terraform validate
terraform plan

# 2. 인프라 배포
terraform apply

# 3. 출력값 확인
terraform output
```

### 5.2 CI/CD 자동 배포

1. 브랜치 생성 후 변경 → PR 생성
2. `terraform-plan` 워크플로우로 변경사항 검토
3. PR merge → `terraform-apply` 또는 `docker-build` 자동 실행

---

## 6. 참고

- preto-1 Terraform: [HRA-1/preto-1/infra/terraform](https://github.com/HRA-1/preto-1/tree/main/infra/terraform)
- preto-1 Workflows: [HRA-1/preto-1/.github/workflows](https://github.com/HRA-1/preto-1/tree/main/.github/workflows)
