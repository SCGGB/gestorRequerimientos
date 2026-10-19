from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from app.application.errors import DocumentGenerationError
from app.application.ports.document_converter import DocumentConverterPort


class LibreofficeDocumentConverter(DocumentConverterPort):
    def __init__(self, binary: str, timeout_seconds: int) -> None:
        self._binary = binary
        self._timeout_seconds = timeout_seconds

    def to_pdf(self, docx: bytes) -> bytes:
        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            source = directory / "document.docx"
            source.write_bytes(docx)
            self._convert(source, directory)
            output = source.with_suffix(".pdf")
            if not output.exists():
                raise DocumentGenerationError(
                    "La conversion a PDF no produjo un archivo."
                )
            data = output.read_bytes()
        if not data:
            raise DocumentGenerationError("El PDF generado esta vacio.")
        return data

    def _convert(self, source: Path, directory: Path) -> None:
        command = [
            self._binary,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(directory),
            str(source),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=self._timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise DocumentGenerationError(
                "No se encontro el binario de LibreOffice para convertir a PDF."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise DocumentGenerationError(
                "La conversion a PDF excedio el tiempo maximo permitido."
            ) from exc
        if result.returncode != 0:
            raise DocumentGenerationError("La conversion a PDF fallo.")
