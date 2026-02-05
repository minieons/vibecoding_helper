"""TypeScript/JavaScript 코드 검증기."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

from vibe.verifiers.base import (
    LanguageVerifier,
    VerifyIssue,
    VerifyLevel,
    VerifyResult,
)


class TypeScriptVerifier(LanguageVerifier):
    """TypeScript 코드 검증기.

    도구:
    - Syntax/Types: tsc --noEmit
    - Lint: eslint
    - Test: vitest 또는 jest
    """

    language = "TypeScript"
    extensions = [".ts", ".tsx"]

    def __init__(self):
        self._project_root: Optional[Path] = None
        self._package_manager: Optional[str] = None

    def check_syntax(self, file_path: Path) -> VerifyResult:
        """TypeScript 문법/타입 검사 (tsc --noEmit)."""
        issues = []

        try:
            # 프로젝트 루트 찾기
            project_root = self._find_project_root(file_path)
            runner = self._get_runner(project_root)

            cmd = runner + ["tsc", "--noEmit", "--pretty", "false"]

            # tsconfig.json이 있으면 해당 설정 사용
            if project_root and (project_root / "tsconfig.json").exists():
                cmd.extend(["--project", str(project_root / "tsconfig.json")])
            else:
                # 단일 파일 검사
                cmd.append(str(file_path))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=project_root or file_path.parent,
            )

            output = result.stdout + result.stderr

            # tsc 출력 파싱
            # 형식: file.ts(10,5): error TS2322: Type ... is not assignable
            for line in output.strip().split("\n"):
                if not line:
                    continue

                # 파일 위치 파싱
                if "): error " in line or "): warning " in line:
                    try:
                        # file.ts(10,5): error TS2322: Message
                        loc_end = line.index(")")
                        loc_start = line.rindex("(", 0, loc_end)

                        file_part = line[:loc_start]
                        loc_part = line[loc_start + 1:loc_end]
                        rest = line[loc_end + 2:].strip()

                        # 라인, 컬럼 파싱
                        loc_parts = loc_part.split(",")
                        line_num = int(loc_parts[0])
                        col_num = int(loc_parts[1]) if len(loc_parts) > 1 else None

                        # 에러/경고 레벨과 메시지
                        if rest.startswith("error "):
                            level = "error"
                            rest = rest[6:]
                        elif rest.startswith("warning "):
                            level = "warning"
                            rest = rest[8:]
                        else:
                            level = "error"

                        # 규칙 코드 (TS2322)
                        rule = None
                        if rest.startswith("TS"):
                            colon_idx = rest.find(":")
                            if colon_idx > 0:
                                rule = rest[:colon_idx]
                                rest = rest[colon_idx + 1:].strip()

                        issues.append(
                            VerifyIssue(
                                level=level,
                                message=rest,
                                file=file_part,
                                line=line_num,
                                column=col_num,
                                rule=rule,
                            )
                        )
                    except (ValueError, IndexError):
                        pass

            success = result.returncode == 0

            return VerifyResult(
                success=success,
                check_type=VerifyLevel.SYNTAX,
                issues=issues,
                output=output,
            )

        except FileNotFoundError:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.SYNTAX,
                output="tsc가 설치되지 않았습니다. TypeScript 검사를 건너뜁니다.",
            )

        except subprocess.TimeoutExpired:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=[VerifyIssue(level="error", message="TypeScript 검사 타임아웃")],
            )

        except Exception as e:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=[VerifyIssue(level="error", message=str(e))],
            )

    def check_types(self, file_path: Path) -> VerifyResult:
        """타입 검사 - TypeScript는 check_syntax에서 함께 처리."""
        return VerifyResult(
            success=True,
            check_type=VerifyLevel.TYPES,
            output="TypeScript 타입 검사는 문법 검사에 포함됩니다.",
        )

    def check_lint(self, file_path: Path, fix: bool = False) -> VerifyResult:
        """린트 검사 (eslint)."""
        issues = []

        try:
            project_root = self._find_project_root(file_path)
            runner = self._get_runner(project_root)

            cmd = runner + ["eslint", "--format", "json"]
            if fix:
                cmd.append("--fix")
            cmd.append(str(file_path))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=project_root or file_path.parent,
            )

            output = result.stdout

            # JSON 출력 파싱
            try:
                eslint_results = json.loads(output)

                for file_result in eslint_results:
                    for msg in file_result.get("messages", []):
                        level = "error" if msg.get("severity") == 2 else "warning"
                        issues.append(
                            VerifyIssue(
                                level=level,
                                message=msg.get("message", ""),
                                file=file_result.get("filePath"),
                                line=msg.get("line"),
                                column=msg.get("column"),
                                rule=msg.get("ruleId"),
                            )
                        )
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 원본 출력 사용
                if result.returncode != 0:
                    issues.append(
                        VerifyIssue(
                            level="error",
                            message=output or result.stderr,
                        )
                    )

            success = result.returncode == 0

            return VerifyResult(
                success=success,
                check_type=VerifyLevel.LINT,
                issues=issues,
                output=output,
                fix_applied=fix and success,
            )

        except FileNotFoundError:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.LINT,
                output="eslint가 설치되지 않았습니다. 린트 검사를 건너뜁니다.",
            )

        except subprocess.TimeoutExpired:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.LINT,
                issues=[VerifyIssue(level="error", message="린트 검사 타임아웃")],
            )

        except Exception as e:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.LINT,
                issues=[VerifyIssue(level="error", message=str(e))],
            )

    def run_tests(self, file_path: Path) -> VerifyResult:
        """관련 테스트 실행 (vitest 또는 jest)."""
        issues = []

        # 테스트 파일 찾기
        test_file = self._find_test_file(file_path)

        if not test_file:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.TEST,
                output=f"관련 테스트 파일을 찾을 수 없습니다: {file_path.name}",
            )

        try:
            project_root = self._find_project_root(file_path)
            runner = self._get_runner(project_root)

            # vitest 또는 jest 시도
            test_runner = self._detect_test_runner(project_root)

            cmd = runner + [test_runner, str(test_file), "--reporter=verbose"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=project_root or file_path.parent,
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0

            if not success:
                issues.append(
                    VerifyIssue(
                        level="error",
                        message="테스트 실패",
                        file=str(test_file),
                    )
                )

            return VerifyResult(
                success=success,
                check_type=VerifyLevel.TEST,
                issues=issues,
                output=output,
            )

        except FileNotFoundError:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.TEST,
                output="테스트 러너(vitest/jest)가 설치되지 않았습니다.",
            )

        except subprocess.TimeoutExpired:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.TEST,
                issues=[VerifyIssue(level="error", message="테스트 타임아웃")],
            )

        except Exception as e:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.TEST,
                issues=[VerifyIssue(level="error", message=str(e))],
            )

    def _find_project_root(self, file_path: Path) -> Optional[Path]:
        """프로젝트 루트 디렉토리 찾기."""
        if self._project_root:
            return self._project_root

        current = file_path.parent

        while current != current.parent:
            if (current / "package.json").exists():
                self._project_root = current
                return current
            if (current / "tsconfig.json").exists():
                self._project_root = current
                return current
            current = current.parent

        return None

    def _get_runner(self, project_root: Optional[Path]) -> list[str]:
        """패키지 매니저에 맞는 실행 명령어 반환."""
        if not project_root:
            return ["npx"]

        if (project_root / "pnpm-lock.yaml").exists():
            return ["pnpm", "exec"]
        elif (project_root / "yarn.lock").exists():
            return ["yarn"]
        elif (project_root / "bun.lockb").exists():
            return ["bun", "x"]
        else:
            return ["npx"]

    def _detect_test_runner(self, project_root: Optional[Path]) -> str:
        """사용 중인 테스트 러너 감지."""
        if not project_root:
            return "vitest"

        package_json = project_root / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                deps = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                }

                if "vitest" in deps:
                    return "vitest"
                elif "jest" in deps:
                    return "jest"
            except (json.JSONDecodeError, KeyError):
                pass

        return "vitest"

    def _find_test_file(self, file_path: Path) -> Optional[Path]:
        """소스 파일에 대응하는 테스트 파일 찾기."""
        stem = file_path.stem
        suffix = file_path.suffix

        # 이미 테스트 파일인 경우
        if stem.endswith(".test") or stem.endswith(".spec"):
            return file_path if file_path.exists() else None

        # 테스트 파일명 생성
        test_names = [
            f"{stem}.test{suffix}",
            f"{stem}.spec{suffix}",
        ]

        # 같은 디렉토리
        for name in test_names:
            test_path = file_path.parent / name
            if test_path.exists():
                return test_path

        # __tests__ 디렉토리
        tests_dir = file_path.parent / "__tests__"
        if tests_dir.is_dir():
            for name in test_names:
                test_path = tests_dir / name
                if test_path.exists():
                    return test_path

        return None


class JavaScriptVerifier(TypeScriptVerifier):
    """JavaScript 코드 검증기.

    TypeScriptVerifier를 상속하여 사용.
    tsc 대신 eslint만 사용.
    """

    language = "JavaScript"
    extensions = [".js", ".jsx", ".mjs", ".cjs"]

    def check_syntax(self, file_path: Path) -> VerifyResult:
        """JavaScript 문법 검사 (node --check 또는 eslint)."""
        issues = []

        try:
            # Node.js의 --check 옵션으로 문법 검사
            result = subprocess.run(
                ["node", "--check", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                # 에러 메시지 파싱
                error_output = result.stderr
                issues.append(
                    VerifyIssue(
                        level="error",
                        message=error_output.strip(),
                        file=str(file_path),
                    )
                )

            return VerifyResult(
                success=result.returncode == 0,
                check_type=VerifyLevel.SYNTAX,
                issues=issues,
                output=result.stderr,
            )

        except FileNotFoundError:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.SYNTAX,
                output="Node.js가 설치되지 않았습니다.",
            )

        except Exception as e:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=[VerifyIssue(level="error", message=str(e))],
            )

    def check_types(self, file_path: Path) -> VerifyResult:
        """JavaScript는 기본적으로 타입 검사 없음."""
        return VerifyResult(
            success=True,
            check_type=VerifyLevel.TYPES,
            output="JavaScript는 타입 검사를 지원하지 않습니다. (JSDoc 또는 TypeScript 사용 권장)",
        )
