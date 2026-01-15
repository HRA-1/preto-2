# Preto-2 Streamlit App - Terraform Infrastructure

## 개요

이 디렉토리는 Preto-2 Streamlit 애플리케이션의 AWS 인프라를 Terraform으로 관리합니다.

## 디렉토리 구조

```
terraform/
├── modules/              # 재사용 가능한 Terraform 모듈
│   ├── autoscaling/     # ECS Auto Scaling 설정
│   ├── ecr/             # ECR 리포지토리 관리
│   ├── ecs/             # ECS 클러스터, 서비스, Task Definition
│   ├── iam/             # IAM 역할 (Task Execution, Task Role)
│   └── network/         # 네트워크 인프라 (ALB, Target Group)
│
└── environments/         # 환경별 설정
    └── prod/            # 프로덕션 환경
```

## 아키텍처

### 모듈 구성

| 모듈 | 역할 | 주요 리소스 |
|------|------|------------|
| ECR | Docker 이미지 저장소 | ECR Repository, Lifecycle Policy |
| IAM | ECS 실행 권한 | Task Execution Role, Task Role |
| ECS | 컨테이너 오케스트레이션 | Cluster, Task Definition, Service |
| Network | 로드 밸런싱 | ALB, Target Group, Listener |
| Auto Scaling | 트래픽 기반 스케일링 | Scaling Target, CPU/Memory Policy |

### S3 Backend

Terraform State를 S3에 저장하여 팀 협업 및 CI/CD를 지원합니다.

```
s3://preto-terraform-state/
└── preto-2/prod/terraform.tfstate
```

### Auto Scaling

트래픽 변화에 따라 ECS 태스크 수를 자동 조절합니다.

> **⚠️ GitHub Actions IAM 권한 필수**
>
> Auto Scaling 리소스 배포 시 `GitHubActionsRole`에 추가 권한이 필요합니다.
> `AmazonECS_FullAccess` 정책만으로는 `application-autoscaling:TagResource` 권한이 부족합니다.
>
> **인라인 정책 추가 필요:**
> ```json
> {
>   "Version": "2012-10-17",
>   "Statement": [
>     {
>       "Effect": "Allow",
>       "Action": "application-autoscaling:*Tag*",
>       "Resource": "*"
>     }
>   ]
> }
> ```

**스케일링 기준:**
| 메트릭 | 목표값 | 스케일 아웃 쿨다운 | 스케일 인 쿨다운 |
|--------|--------|-------------------|-----------------|
| CPU 사용률 | 70% | 60초 | 300초 |
| 메모리 사용률 | 70% | 60초 | 300초 |

**태스크 범위:** 최소 1개 ~ 최대 4개

**트래픽 분산 흐름:**
```
User Request → ALB → Target Group (라운드 로빈) → Task 1~4
```

- 스케일 아웃: CPU 또는 메모리 중 하나라도 70% 초과 시 태스크 추가
- 스케일 인: CPU와 메모리 모두 70% 미만일 때 태스크 감소
- 새 태스크는 Target Group에 자동 등록되어 ALB가 트래픽 분산

## 사용 방법

### 1. 초기화

```bash
cd environments/prod
terraform init
```

### 2. 실행 계획 확인

```bash
terraform plan
```

### 3. 인프라 배포

```bash
terraform apply
```

### 4. 출력값 확인

```bash
terraform output
```

## 주요 출력값

| 출력 | 설명 |
|------|------|
| `ecr_repository_url` | ECR 리포지토리 URL |
| `ecs_cluster_name` | ECS 클러스터 이름 |
| `ecs_service_name` | ECS 서비스 이름 |
| `alb_dns_name` | ALB DNS (애플리케이션 접속 URL) |
| `autoscaling_enabled` | Auto Scaling 활성화 여부 |
| `autoscaling_min_capacity` | 최소 태스크 수 |
| `autoscaling_max_capacity` | 최대 태스크 수 |

## 모듈 간 의존성

```
ECR → ECS (container_image)
IAM → ECS (task_execution_role_arn, task_role_arn)
Network → ECS (subnet_ids, security_group_id, target_group_arn)
ECS → Auto Scaling (cluster_name, service_name)
```

## 변수 재정의

환경별로 다른 값을 사용하려면 `terraform.tfvars` 파일 생성:

```hcl
# environments/prod/terraform.tfvars
ecs_cpu    = "4096"
ecs_memory = "16384"
ecs_desired_count = 2

# Auto Scaling 설정
autoscaling_enabled      = true
autoscaling_min_capacity = 1
autoscaling_max_capacity = 4
autoscaling_cpu_target   = 70
autoscaling_memory_target = 70
```

## 참고 자료

- [Terraform 모듈 문서](https://developer.hashicorp.com/terraform/language/modules)
- [Terraform S3 Backend](https://developer.hashicorp.com/terraform/language/backend/s3)
- [AWS Provider 문서](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
