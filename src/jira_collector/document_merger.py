from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from docx import Document
from docxcompose.composer import Composer

# Las extensiones soportadas para unir documentos son .doc y .docx, ya que son los formatos de Word que permiten conservar el formato, tablas e imagenes.
SUPPORTED_EXTENSIONS = {".doc", ".docx"}

# Funcion privada que convierte un archivo .doc a .docx usando LibreOffice en modo headless (sin interfaz grafica)
def _convert_doc_to_docx(source: Path, destination_dir: Path) -> Path:
    converter = shutil.which("libreoffice") or shutil.which("soffice")
    if converter is None:
        raise RuntimeError("Para procesar archivos .doc se necesita LibreOffice instalado")

    subprocess.run(
        [
            converter,
            "--headless",
            "--convert-to",
            "docx",
            "--outdir",
            str(destination_dir),
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    # El archivo convertido se guarda en el directorio de destino con la misma base de nombre pero con extension .docx
    converted = destination_dir / f"{source.stem}.docx"
    if not converted.exists():
        raise RuntimeError(f"LibreOffice no pudo convertir {source.name}")
    return converted

# Funcion que une documentos Word completos, conservando texto, tablas e imágenes. Recibe una lista de tuplas donde cada tupla contiene la ruta del archivo descargado y el titulo del issue, y un archivo de salida donde se guardara el documento final unificado.
def merge_documents(documents: list[Path], output_file: Path) -> int:
    """Une documentos Word completos, conservando texto, tablas e imágenes."""
    with TemporaryDirectory() as temporary_directory:
        temporary_dir = Path(temporary_directory)
        master = Document()
        composer = Composer(master)
        included = 0

        for source in documents:
            suffix = source.suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                continue
            converted = (
                _convert_doc_to_docx(source, temporary_dir)
                if suffix == ".doc"
                else source
            )
            if included:
                composer.doc.add_page_break()
            composer.append(Document(converted))
            included += 1

        output_file.parent.mkdir(parents=True, exist_ok=True)
        composer.save(output_file)
        return included