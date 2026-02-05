"""Java 코드 검증기."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

from vibe.verifiers.base import (
    LanguageVerifier,
    VerifyIssue,
    VerifyLevel,
    VerifyResult,
)


class JavaVerifier(LanguageVerifier):
    """Java 코드 검증기.

    도구:
    - Syntax/Types: javac
    - Lint: checkstyle (선택적)
    - Test: JUnit (maven/gradle)
    """

    language = "Java"
    extensions = [".java"]

    def __init__(self):
        self._project_root: Optional[Path] = None
        self._build_tool: Optional[str] = None  # maven, gradle, or None

    def check_syntax(self, file_path: Path) -> VerifyResult:
        """Java 문법/타입 검사 (javac)."""
        issues = []

        try:
            # javac로 컴파일 검사 (-d /dev/null로 출력 없이)
            result = subprocess.run(
                [
                    "javac",
                    "-Xlint:all",
                    "-d", "/tmp",  # 임시 출력 디렉토리
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr

            # javac 출력 파싱
            # 형식: file.java:10: error: ';' expected
            for line in output.strip().split("\n"):
                if not line:
                    continue

                # 파일:라인: 레벨: 메시지 형식
                match = re.match(r"(.+\.java):(\d+): (error|warning): (.+)", line)
                if match:
                    file_part, line_num, level, message = match.groups()
                    issues.append(
                        VerifyIssue(
                            level=level,
                            message=message,
                            file=file_part,
                            line=int(line_num),
                        )
                    )

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
                output="javac가 설치되지 않았습니다. Java 검사를 건너뜁니다.",
            )

        except subprocess.TimeoutExpired:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=[VerifyIssue(level="error", message="Java 컴파일 타임아웃")],
            )

        except Exception as e:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=[VerifyIssue(level="error", message=str(e))],
            )

    def check_types(self, file_path: Path) -> VerifyResult:
        """타입 검사 - Java는 check_syntax에서 함께 처리."""
        return VerifyResult(
            success=True,
            check_type=VerifyLevel.TYPES,
            output="Java 타입 검사는 문법 검사(javac)에 포함됩니다.",
        )

    def check_lint(self, file_path: Path, fix: bool = False) -> VerifyResult:
        """린트 검사 (checkstyle)."""
        issues = []

        try:
            # checkstyle 실행
            result = subprocess.run(
                [
                    "checkstyle",
                    "-c", "/google_checks.xml",  # Google 스타일 가이드
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr

            # checkstyle 출력 파싱
            # 형식: [WARN] file.java:10:5: ... [RuleName]
            for line in output.strip().split("\n"):
                match = re.match(
                    r"\[(WARN|ERROR)\] (.+\.java):(\d+)(?::(\d+))?: (.+?) \[(\w+)\]",
                    line
                )
                if match:
                    level_str, file_part, line_num, col_num, message, rule = match.groups()
                    level = "warning" if level_str == "WARN" else "error"

                    issues.append(
                        VerifyIssue(
                            level=level,
                            message=message,
                            file=file_part,
                            line=int(line_num),
                            column=int(col_num) if col_num else None,
                            rule=rule,
                        )
                    )

            # checkstyle은 경고만 있어도 성공으로 처리
            success = not any(i.level == "error" for i in issues)

            return VerifyResult(
                success=success,
                check_type=VerifyLevel.LINT,
                issues=issues,
                output=output,
            )

        except FileNotFoundError:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.LINT,
                output="checkstyle이 설치되지 않았습니다. 린트 검사를 건너뜁니다.",
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
        """관련 테스트 실행 (Maven/Gradle)."""
        issues = []

        project_root = self._find_project_root(file_path)
        build_tool = self._detect_build_tool(project_root)

        if not build_tool:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.TEST,
                output="Maven/Gradle 프로젝트가 아닙니다. 테스트를 건너뜁니다.",
            )

        # 테스트 클래스 찾기
        test_class = self._find_test_class(file_path, project_root)

        try:
            if build_tool == "maven":
                cmd = ["mvn", "test"]
                if test_class:
                    cmd.extend(["-Dtest=" + test_class])
            else:  # gradle
                cmd = ["./gradlew", "test"]
                if test_class:
                    cmd.extend(["--tests", test_class])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 테스트는 오래 걸릴 수 있음
                cwd=project_root,
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0

            if not success:
                issues.append(
                    VerifyIssue(
                        level="error",
                        message="테스트 실패",
                        file=str(file_path),
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
                output=f"{build_tool}이 설치되지 않았습니다.",
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
            if (current / "pom.xml").exists():
                self._project_root = current
                return current
            if (current / "build.gradle").exists():
                self._project_root = current
                return current
            if (current / "build.gradle.kts").exists():
                self._project_root = current
                return current
            current = current.parent

        return None

    def _detect_build_tool(self, project_root: Optional[Path]) -> Optional[str]:
        """빌드 도구 감지."""
        if not project_root:
            return None

        if self._build_tool:
            return self._build_tool

        if (project_root / "pom.xml").exists():
            self._build_tool = "maven"
        elif (project_root / "build.gradle").exists() or (project_root / "build.gradle.kts").exists():
            self._build_tool = "gradle"

        return self._build_tool

    def _find_test_class(self, file_path: Path, project_root: Optional[Path]) -> Optional[str]:
        """소스 파일에 대응하는 테스트 클래스 찾기."""
        if not project_root:
            return None

        # 클래스 이름 추출 (파일명에서)
        class_name = file_path.stem

        # 이미 테스트 클래스인 경우
        if class_name.endswith("Test") or class_name.startswith("Test"):
            return class_name

        # 테스트 클래스명 생성
        test_class_name = f"{class_name}Test"

        # src/test/java 에서 검색
        test_dir = project_root / "src" / "test" / "java"
        if test_dir.is_dir():
            for test_file in test_dir.rglob(f"{test_class_name}.java"):
                # 패키지 경로 포함한 클래스명 반환
                rel_path = test_file.relative_to(test_dir)
                return str(rel_path.with_suffix("")).replace("/", ".")

        return None
