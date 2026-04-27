from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from re import sub


@dataclass(frozen=True)
class StagedEvidenceArtifact:
    artifact_uri: str
    checksum_sha256: str
    local_path: Path


class TelegramEvidenceArtifactStager:
    def __init__(self, root_directory: Path) -> None:
        self._root_directory = root_directory

    async def stage_document(self, bot, document) -> StagedEvidenceArtifact:
        if bot is None:
            raise ValueError("증빙 파일을 stage 하려면 bot 인스턴스가 필요합니다.")
        if document is None:
            raise ValueError("증빙 파일 정보가 없습니다.")

        self._root_directory.mkdir(parents=True, exist_ok=True)
        suffix = Path(document.file_name or "").suffix.lower()
        if not suffix:
            suffix = ".bin"
        safe_stem = sub(r"[^A-Za-z0-9_.-]+", "_", document.file_unique_id or document.file_id or "artifact")
        local_path = self._root_directory / f"{safe_stem}{suffix}"

        telegram_file = await bot.get_file(document.file_id)
        await telegram_file.download_to_drive(custom_path=str(local_path))

        checksum = _compute_sha256(local_path)
        return StagedEvidenceArtifact(
            artifact_uri=local_path.resolve().as_uri(),
            checksum_sha256=checksum,
            local_path=local_path.resolve(),
        )


def _compute_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
