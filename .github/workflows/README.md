# GitHub Actions CI/CD

## 워크플로우 개요

| 워크플로우 | 트리거 | 목적 |
|-----------|--------|------|
| `terraform-plan.yml` | PR (infra 변경) | Plan 결과를 PR 코멘트로 표시 |
| `terraform-apply.yml` | main 푸시 (infra 변경) | 인프라 자동 적용 |
| `docker-build.yml` | main 푸시 (app 변경) | 이미지 빌드 및 ECS 배포 |

---

## OIDC 인증

GitHub Actions에서 AWS에 접근할 때 OIDC (OpenID Connect) 방식을 사용합니다.

### 장점

- Access Key 저장 불필요 (유출 위험 없음)
- 임시 자격 증명 (자동 만료)
- 특정 Repository/Branch만 허용 가능

### 동작 순서

1. GitHub Actions가 OIDC 토큰 생성
2. `configure-aws-credentials` 액션이 토큰으로 AWS STS 호출
3. AWS가 토큰 검증 후 임시 자격 증명 발급
4. 이후 step에서 AWS 리소스 접근 가능

---

## 설정 방법

### 1. AWS IAM Trust Policy 업데이트

기존 `GitHubActionsRole`의 Trust Policy에 preto-2 리포지토리를 추가합니다:

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

### 2. GitHub Repository Secret 설정

1. GitHub Repository 페이지 접속
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** 클릭
4. 입력:
   - Name: `AWS_ROLE_ARN`
   - Value: `arn:aws:iam::<ACCOUNT_ID>:role/GitHubActionsRole`

### 3. GitHub Environment 설정 (선택)

프로덕션 배포 시 승인 프로세스를 추가하려면:

1. **Settings** → **Environments** → **New environment**
2. Name: `prod`
3. **Environment protection rules**:
   - Required reviewers → 승인자 추가
   - Wait timer → 배포 전 대기 시간

---

## 워크플로우 상세

### terraform-plan.yml

**트리거**: `infra/terraform/**` 경로 변경 시 PR 생성

**기능**:
- Terraform format 검사
- Terraform init/validate/plan 실행
- Plan 결과를 PR 코멘트로 표시

### terraform-apply.yml

**트리거**: `infra/terraform/**` 경로 변경 후 PR merge

**기능**:
- Terraform init/plan/apply 실행
- 인프라 자동 배포

### docker-build.yml

**트리거**: `src/**`, `Dockerfile` 등 변경 후 PR merge

**기능**:
- Docker 이미지 빌드 (ARM64)
- ECR에 이미지 푸시
- ECS 서비스 업데이트
- 서비스 안정화 대기

---

## 트러블슈팅

### OIDC 인증 실패

```
Error: Could not assume role with OIDC
```

**확인사항**:
1. Trust Policy의 `sub` 조건이 정확한지
2. OIDC Provider가 생성되어 있는지
3. 워크플로우에 `permissions.id-token: write` 있는지

### ECS 배포 실패

```
service was unable to place a task
```

**확인사항**:
- ECR에 이미지 존재하는지
- Task Definition의 CPU/Memory 설정
- 서브넷이 퍼블릭인지, NAT Gateway가 있는지

---

## 참고 자료

- [GitHub OIDC 공식 문서](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [AWS IAM OIDC Provider](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
- [aws-actions/configure-aws-credentials](https://github.com/aws-actions/configure-aws-credentials)
