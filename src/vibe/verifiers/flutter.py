"""Flutter/Dart 코드 검증기."""

from __future__ import annotations

import json
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


class DartVerifier(LanguageVerifier):
    """Dart 코드 검증기.

    도구:
    - Syntax/Types/Lint: dart analyze
    - Test: dart test
    """

    language = "Dart"
    extensions = [".dart"]

    def __init__(self):
        self._project_root: Optional[Path] = None
        self._is_flutter: bool = False

    def check_syntax(self, file_path: Path) -> VerifyResult:
        """Dart 문법/타입 검사 (dart analyze)."""
        issues = []

        try:
            project_root = self._find_project_root(file_path)

            # dart analyze 실행
            cmd = ["dart", "analyze", "--format=json"]

            if project_root:
                cmd.append(str(project_root))
            else:
                cmd.append(str(file_path))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=project_root or file_path.parent,
            )

            output = result.stdout

            # JSON 형식 파싱 시도
            try:
                # dart analyze --format=json 출력
                for line in output.strip().split("\n"):
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)

                        if "diagnostics" in data:
                            for diag in data["diagnostics"]:
                                severity = diag.get("severity", "INFO")
                                level = "error" if severity == "ERROR" else "warning"

                                location = diag.get("location", {})

                                issues.append(
                                    VerifyIssue(
                                        level=level,
                                        message=diag.get("problemMessage", ""),
                                        file=location.get("file"),
                                        line=location.get("range", {}).get("start", {}).get("line"),
                                        column=location.get("range", {}).get("start", {}).get("column"),
                                        rule=diag.get("code"),
                                    )
                                )
                    except json.JSONDecodeError:
                        # JSON이 아닌 라인은 텍스트 형식으로 파싱
                        self._parse_text_output(line, issues)

            except Exception:
                # JSON 파싱 실패 시 텍스트 형식으로 파싱
                self._parse_text_output(output, issues)

            success = result.returncode == 0

            return VerifyResult(
                success=success,
                check_type=VerifyLevel.SYNTAX,
                issues=issues,
                output=output + result.stderr,
            )

        except FileNotFoundError:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.SYNTAX,
                output="dart가 설치되지 않았습니다. Dart 검사를 건너뜁니다.",
            )

        except subprocess.TimeoutExpired:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=[VerifyIssue(level="error", message="Dart 분석 타임아웃")],
            )

        except Exception as e:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=[VerifyIssue(level="error", message=str(e))],
            )

    def _parse_text_output(self, output: str, issues: list) -> None:
        """텍스트 형식 출력 파싱."""
        # 형식: info • message • file.dart:10:5 • rule_name
        # 또는: error • message • file.dart:10:5 • rule_name
        for line in output.split("\n"):
            match = re.match(
                r"\s*(info|warning|error)\s+[•-]\s+(.+?)\s+[•-]\s+(.+?):(\d+):(\d+)\s+[•-]\s+(\w+)",
                line
            )
            if match:
                level_str, message, file_path, line_num, col_num, rule = match.groups()
                level = "error" if level_str == "error" else "warning"

                issues.append(
                    VerifyIssue(
                        level=level,
                        message=message.strip(),
                        file=file_path,
                        line=int(line_num),
                        column=int(col_num),
                        rule=rule,
                    )
                )

    def check_types(self, file_path: Path) -> VerifyResult:
        """타입 검사 - Dart는 check_syntax에서 함께 처리."""
        return VerifyResult(
            success=True,
            check_type=VerifyLevel.TYPES,
            output="Dart 타입 검사는 dart analyze에 포함됩니다.",
        )

    def check_lint(self, file_path: Path, fix: bool = False) -> VerifyResult:
        """린트 검사 - Dart는 dart analyze에 포함."""
        issues = []

        try:
            project_root = self._find_project_root(file_path)

            cmd = ["dart", "fix"]
            if fix:
                cmd.append("--apply")
            else:
                cmd.append("--dry-run")

            if project_root:
                cmd.append(str(project_root))
            else:
                cmd.append(str(file_path.parent))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=project_root or file_path.parent,
            )

            output = result.stdout + result.stderr

            # dart fix 출력 파싱
            # "Computing fixes in ..." / "X fixes applied"
            if "Nothing to fix" in output:
                return VerifyResult(
                    success=True,
                    check_type=VerifyLevel.LINT,
                    output="린트 이슈 없음",
                )

            # 수정 적용됨
            if fix and "fixes" in output.lower():
                return VerifyResult(
                    success=True,
                    check_type=VerifyLevel.LINT,
                    output=output,
                    fix_applied=True,
                )

            return VerifyResult(
                success=True,
                check_type=VerifyLevel.LINT,
                issues=issues,
                output=output,
            )

        except FileNotFoundError:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.LINT,
                output="dart가 설치되지 않았습니다.",
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
        """관련 테스트 실행 (dart test)."""
        issues = []

        project_root = self._find_project_root(file_path)
        is_flutter = self._check_is_flutter(project_root)

        # 테스트 파일 찾기
        test_file = self._find_test_file(file_path, project_root)

        try:
            if is_flutter:
                cmd = ["flutter", "test"]
            else:
                cmd = ["dart", "test"]

            if test_file:
                cmd.append(str(test_file))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=project_root or file_path.parent,
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0

            if not success:
                issues.append(
                    VerifyIssue(
                        level="error",
                        message="테스트 실패",
                        file=str(test_file) if test_file else str(file_path),
                    )
                )

            return VerifyResult(
                success=success,
                check_type=VerifyLevel.TEST,
                issues=issues,
                output=output,
            )

        except FileNotFoundError:
            tool = "flutter" if is_flutter else "dart"
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.TEST,
                output=f"{tool}이 설치되지 않았습니다.",
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
            if (current / "pubspec.yaml").exists():
                self._project_root = current
                return current
            current = current.parent

        return None

    def _check_is_flutter(self, project_root: Optional[Path]) -> bool:
        """Flutter 프로젝트인지 확인."""
        if project_root is None:
            return False

        pubspec = project_root / "pubspec.yaml"
        if pubspec.exists():
            try:
                content = pubspec.read_text()
                return "flutter:" in content or "sdk: flutter" in content
            except Exception:
                pass

        return False

    def _find_test_file(self, file_path: Path, project_root: Optional[Path]) -> Optional[Path]:
        """소스 파일에 대응하는 테스트 파일 찾기."""
        stem = file_path.stem

        # 이미 테스트 파일인 경우
        if stem.endswith("_test"):
            return file_path if file_path.exists() else None

        # 테스트 파일명 생성
        test_name = f"{stem}_test.dart"

        # 같은 디렉토리
        same_dir = file_path.parent / test_name
        if same_dir.exists():
            return same_dir

        # test/ 디렉토리에서 검색
        if project_root:
            test_dir = project_root / "test"
            if test_dir.is_dir():
                # test/file_test.dart
                direct = test_dir / test_name
                if direct.exists():
                    return direct

                # test/unit/file_test.dart 등
                for test_file in test_dir.rglob(test_name):
                    return test_file

        return None


class FlutterVerifier(DartVerifier):
    """Flutter 코드 검증기.

    DartVerifier를 상속하여 Flutter 특화 기능 추가.
    """

    language = "Flutter"
    extensions = [".dart"]  # 동일하지만 Flutter 프로젝트에서 우선 사용

    def check_syntax(self, file_path: Path) -> VerifyResult:
        """Flutter 분석 (flutter analyze)."""
        issues = []

        try:
            project_root = self._find_project_root(file_path)

            # Flutter 프로젝트인지 확인
            if not self._check_is_flutter(project_root):
                # Flutter가 아니면 일반 Dart 검증기 사용
                return super().check_syntax(file_path)

            # flutter analyze 실행
            result = subprocess.run(
                ["flutter", "analyze", "--no-pub"],
                capture_output=True,
                text=True,
                timeout=180,
                cwd=project_root or file_path.parent,
            )

            output = result.stdout + result.stderr

            # flutter analyze 출력 파싱
            # 형식: info • message • lib/file.dart:10:5 • rule_name
            self._parse_text_output(output, issues)

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
                output="flutter가 설치되지 않았습니다. Flutter 검사를 건너뜁니다.",
            )

        except subprocess.TimeoutExpired:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=[VerifyIssue(level="error", message="Flutter 분석 타임아웃")],
            )

        except Exception as e:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.SYNTAX,
                issues=[VerifyIssue(level="error", message=str(e))],
            )

    def check_lint(self, file_path: Path, fix: bool = False) -> VerifyResult:
        """린트 검사 (dart fix)."""
        project_root = self._find_project_root(file_path)

        if not self._check_is_flutter(project_root):
            return super().check_lint(file_path, fix)

        issues = []

        try:
            cmd = ["dart", "fix"]
            if fix:
                cmd.append("--apply")
            else:
                cmd.append("--dry-run")

            cmd.append(str(project_root or file_path.parent))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=project_root or file_path.parent,
            )

            output = result.stdout + result.stderr
            fix_applied = fix and ("applied" in output.lower() or "fix" in output.lower())

            return VerifyResult(
                success=True,
                check_type=VerifyLevel.LINT,
                issues=issues,
                output=output,
                fix_applied=fix_applied,
            )

        except FileNotFoundError:
            return VerifyResult(
                success=True,
                check_type=VerifyLevel.LINT,
                output="dart가 설치되지 않았습니다.",
            )

        except Exception as e:
            return VerifyResult(
                success=False,
                check_type=VerifyLevel.LINT,
                issues=[VerifyIssue(level="error", message=str(e))],
            )
