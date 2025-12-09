"""Report artifact storage helpers.

帳票ファイル (Excel / PDF) をディスクへ保存し、署名付きURLを生成する責務を担う。

初心者向け豆知識:
    - 単一責務 (Single Responsibility Principle): このモジュールは保存と署名URL生成に専念する。
    - 生成されたトークンごとに専用ディレクトリを使うことで、同時実行でもファイル名が衝突しない。
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import hmac
from pathlib import Path
import secrets
import time
from typing import Dict, Optional
from urllib.parse import quote, unquote

from app.settings import settings


def _sanitize_segment(value: str) -> str:
    """👶 ファイルパスに使えない文字を安全な形に置き換える関数です。"""
    allow = {"-", "_"}
    sanitized = [ch if ch.isalnum() or ch in allow else "-" for ch in value.strip()]
    filtered = "".join(sanitized).strip("-_")
    return filtered or "report"


@dataclass(frozen=True)
class ArtifactLocation:
    """帳票アーティファクトの保存場所を表す不変オブジェクト。

    👶 このクラスは「どこに保存するか」の情報をひとまとめに持っています。
    """

    root_dir: Path
    report_key: str
    report_date: str
    token: str
    file_base: str

    @property
    def directory(self) -> Path:
        """👶 ファイルを保存する最終ディレクトリを返します。"""
        return self.root_dir / _sanitize_segment(self.report_key) / _sanitize_segment(self.report_date) / self.token

    def relative_path(self, filename: str) -> str:
        """保存先ディレクトリからの相対パスを返す。"""
        return "/".join(
            [
                _sanitize_segment(self.report_key),
                _sanitize_segment(self.report_date),
                self.token,
                filename,
            ]
        )

    def file_path(self, suffix: str) -> Path:
        """👶 Excel(.xlsx) や PDF(.pdf) のフルパスを作る便利関数です。"""
        return self.directory / f"{self.file_base}{suffix}"


class UrlSigner:
    """簡易な HMAC 署名付き URL を生成・検証するヘルパー。"""

    def __init__(self, secret: str, url_prefix: str, ttl_seconds: int) -> None:
        self._secret = secret.encode("utf-8")
        self._url_prefix = url_prefix.rstrip("/")
        self._ttl_seconds = max(30, ttl_seconds)  # 👶 有効期限が極端に短すぎないようにします

    def _sign(self, relative_path: str, disposition: str, expires: int) -> str:
        payload = f"{relative_path}|{disposition}|{expires}".encode("utf-8")
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()

    def create_url(self, relative_path: str, *, disposition: str) -> str:
        """署名付き URL を生成する。"""
        expires = int(time.time()) + self._ttl_seconds
        signature = self._sign(relative_path, disposition, expires)
        safe_path = quote(relative_path, safe="/")
        return (
            f"{self._url_prefix}/{safe_path}?expires={expires}&disposition={disposition}&signature={signature}"
        )

    def verify(self, relative_path: str, *, disposition: str, expires: int, signature: str) -> bool:
        if expires < int(time.time()):
            return False
        expected = self._sign(relative_path, disposition, expires)
        return hmac.compare_digest(expected, signature)

    @property
    def url_prefix(self) -> str:
        return self._url_prefix


class ReportArtifactStorage:
    """帳票ファイルの保存と URL 生成を担当するクラス。"""

    def __init__(self, root_dir: Path, signer: UrlSigner) -> None:
        self.root_dir = root_dir
        self.signer = signer

    def allocate(self, report_key: str, report_date: str) -> ArtifactLocation:
        # 帳簿作成日付をトークンに使用（時刻部分のみ現在時刻）
        token = f"{report_date.replace('-', '')}_{time.strftime('%H%M%S')}-{secrets.token_hex(4)}"
        # 英語キーをそのまま使用（ASCII安全、フロントエンドで日本語変換）
        file_base = _sanitize_segment(f"{report_key}-{report_date}")
        location = ArtifactLocation(self.root_dir, report_key, report_date, token, file_base)
        location.directory.mkdir(parents=True, exist_ok=True)
        return location

    def save_excel(self, location: ArtifactLocation, content: bytes) -> Path:
        target = location.file_path(".xlsx")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    def save_pdf(self, location: ArtifactLocation, content: bytes) -> Path:
        target = location.file_path(".pdf")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    def build_payload(self, location: ArtifactLocation, *, excel_exists: bool, pdf_exists: bool) -> Dict[str, str]:
        payload: Dict[str, str] = {
            "report_token": location.token,
            "excel_download_url": "",
            "pdf_preview_url": "",
        }
        excel_filename = f"{location.file_base}.xlsx"
        pdf_filename = f"{location.file_base}.pdf"
        if excel_exists:
            payload["excel_download_url"] = self.signer.create_url(
                location.relative_path(excel_filename), disposition="attachment"
            )
        if pdf_exists:
            payload["pdf_preview_url"] = self.signer.create_url(
                location.relative_path(pdf_filename), disposition="inline"
            )
        return payload

    def resolve(self, relative_path: str) -> Optional[Path]:
        """URL で渡された相対パスから実際のファイルパスを復元する。"""
        raw = Path(unquote(relative_path))
        parts = [segment for segment in raw.parts if segment not in {"..", ""}]
        safe_relative = Path(*parts)
        full_path = (self.root_dir / safe_relative).resolve()
        try:
            full_path.relative_to(self.root_dir)
        except ValueError:
            return None
        return full_path


@lru_cache(maxsize=1)
def get_url_signer() -> UrlSigner:
    """UrlSigner をシングルトンとして提供する。"""
    return UrlSigner(
        secret=settings.report_artifact_secret,
        url_prefix=settings.report_artifact_url_prefix,
        ttl_seconds=settings.report_artifact_url_ttl,
    )


@lru_cache(maxsize=1)
def get_report_artifact_storage() -> ReportArtifactStorage:
    """ReportArtifactStorage をシングルトンとして提供する。"""
    root_dir = settings.report_artifact_root_dir / "reports"
    root_dir.mkdir(parents=True, exist_ok=True)
    return ReportArtifactStorage(root_dir=root_dir, signer=get_url_signer())