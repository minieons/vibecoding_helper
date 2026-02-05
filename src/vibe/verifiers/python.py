"""Python 코드 검증기."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from vibe.verifiers.base import (
    LanguageVerifier,
    VerifyIssue,
    VerifyLevel,
    VerifyResult,
)


class PythonVerifier(LanguageVerifier):
    """Python 코드 검증기.

    도구:
    - Syntax: ast.parse()
    - Types: mypy
    - Lint: ruff
    - Test: pytest
    """

    language = "Python"
    extensions = [".py", ".pyi"]

    def check_syntax(self, file_path: Path) -> VerifyResult:
        """Python 문법 검사 (ast.parse)."""
        issues = []

        try:
            source = file_path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(file_path))

            return VerifyResult(
                success=True,
                check_type=VerifyLevel.SYNTAX,
                output="문법 검사 통과",
            )

        except SyntaxError as e:
            issues.append(
                VerifyIssue(
                    level="error",
                    message=e.msg or "Syntax error",
                    file=str(file_path),
                    line=e.lineno,
                    column=e.offset,
                )
            )
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=issues,
                output=str(e),
            )

        except Exception as e:
            issues.append(
                VerifyIssue(
                    level="error",
                    message=str(e),
                    file=str(file_path),
                )
            )
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=issues,
                output=str(e),
            )

    def check_types(self, file_path: Path) -> VerifyResult:
        """타입 검사 (mypy)."""
        issues = []

        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "mypy",
                    "--ignore-missing-imports",
                    "--no-error-summary",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr

            # mypy 출력 파싱
            for line in output.strip().split("\n"):
                if not line or line.startswith("Success"):
                    continue

                # 형식: file.py:10: error: Message
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    try:
                        line_num = int(parts[1])
                        level = "error" if "error" in parts[2] else "warning"
                        message = parts[3].strip()

                        issues.append(
                            VerifyIssue(
                                level=level,
                                message=message,
                                file=parts[0],
                                line=line_num,
                            )
                        )
                    except (ValueError, IndexError):
                        pass

            success = result.returncode == 0

            return VerifyResult(
                success=success,
                check_type=VerifyLevel.TYPES,
                issues=issues,
                output=output,
            )

        except FileNotFoundError:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.TYPES,
                output="mypy가 설치되지 않았습니다. 타입 검사를 건너뜁니다.",
            )

        except subprocess.TimeoutExpired:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.TYPES,
                issues=[VerifyIssue(level="error", message="타입 검사 타임아웃")],
            )

        except Exception as e:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.TYPES,
                issues=[VerifyIssue(level="error", message=str(e))],
            )

    def check_lint(self, file_path: Path, fix: bool = False) -> VerifyResult:
        """린트 검사 (ruff)."""
        issues = []

        try:
            cmd = [sys.executable, "-m", "ruff", "check"]
            if fix:
                cmd.append("--fix")
            cmd.append(str(file_path))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr

            # ruff 출력 파싱
            for line in output.strip().split("\n"):
                if not line:
                    continue

                # 형식: file.py:10:5: E501 Line too long
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    try:
                        line_num = int(parts[1])
                        col_num = int(parts[2])
                        rest = parts[3].strip()

                        # 규칙 코드와 메시지 분리
                        rule_parts = rest.split(" ", 1)
                        rule = rule_parts[0] if rule_parts else ""
                        message = rule_parts[1] if len(rule_parts) > 1 else rest

                        issues.append(
                            VerifyIssue(
                                level="warning",
                                message=message,
                                file=parts[0],
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
                check_type=VerifyLevel.LINT,
                issues=issues,
                output=output,
                fix_applied=fix and success,
            )

        except FileNotFoundError:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.LINT,
                output="ruff가 설치되지 않았습니다. 린트 검사를 건너뜁니다.",
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
        """관련 테스트 실행 (pytest)."""
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
            result = subprocess.run(
                [
                    sys.executable, "-m", "pytest",
                    str(test_file),
                    "-v",
                    "--tb=short",
                ],
                capture_output=True,
                text=True,
                timeout=120,
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
                output="pytest가 설치되지 않았습니다. 테스트를 건너뜁니다.",
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

    def _find_test_file(self, file_path: Path) -> Optional[Path]:
        """소스 파일에 대응하는 테스트 파일 찾기."""
        # 이미 테스트 파일인 경우
        if file_path.name.startswith("test_"):
            return file_path if file_path.exists() else None

        # 테스트 파일명 생성: config.py -> test_config.py
        test_name = f"test_{file_path.name}"

        # 같은 디렉토리
        same_dir = file_path.parent / test_name
        if same_dir.exists():
            return same_dir

        # tests/ 디렉토리 검색
        project_root = self._find_project_root(file_path)
        if project_root:
            for tests_dir in ["tests", "test"]:
                test_path = project_root / tests_dir
                if test_path.is_dir():
                    # tests/test_config.py
                    direct = test_path / test_name
                    if direct.exists():
                        return direct

                    # tests/unit/test_config.py
                    for subdir in test_path.iterdir():
                        if subdir.is_dir():
                            sub_test = subdir / test_name
                            if sub_test.exists():
                                return sub_test

        return None

    def _find_project_root(self, file_path: Path) -> Optional[Path]:
        """프로젝트 루트 디렉토리 찾기."""
        current = file_path.parent

        while current != current.parent:
            # pyproject.toml, setup.py, .git 등으로 루트 판단
            if (current / "pyproject.toml").exists():
                return current
            if (current / "setup.py").exists():
                return current
            if (current / ".git").exists():
                return current
            current = current.parent

        return None


def check_imports(file_path: Path) -> VerifyResult:
    """import 문 검증 (실제 import 시도)."""
    issues = []

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append((node.module, node.lineno))

        # 각 import 검증
        for module_name, line_no in imports:
            try:
                __import__(module_name.split(".")[0])
            except ImportError as e:
                issues.append(
                    VerifyIssue(
                        level="warning",
                        message=f"Import 실패: {module_name} - {e}",
                        file=str(file_path),
                        line=line_no,
                    )
                )

        return VerifyResult(
            success=len([i for i in issues if i.level == "error"]) == 0,
            check_type=VerifyLevel.SYNTAX,
            issues=issues,
            output=f"검사한 import: {len(imports)}개",
        )

    except Exception as e:
        return VerifyResult(
            success=False,
            check_type=VerifyLevel.SYNTAX,
            issues=[VerifyIssue(level="error", message=str(e))],
        )
