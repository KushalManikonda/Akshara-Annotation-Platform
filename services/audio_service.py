import os
import shutil
import uuid
import zipfile

from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from database.database import SessionLocal
from database.models import AudioFile, Dataset, Annotation
from database.enums import AudioStatus
import config
from utils.logger import logger
from utils.metadata_parser import parse_metadata_from_extraction

# ==========================================================
# Storage
# ==========================================================

BASE_AUDIO_PATH = config.BASE_AUDIO_PATH

# ==========================================================
# Database Session
# ==========================================================

def get_db() -> Session:
    return SessionLocal()


# ==========================================================
# Get All Audio
# ==========================================================

def get_all_audio() -> list[AudioFile]:

    db = get_db()

    try:
        return (
            db.query(AudioFile)
            .order_by(AudioFile.id.desc())
            .all()
        )

    finally:
        db.close()

def get_all_datasets():

    db = get_db()

    try:
        return (
            db.query(Dataset)
            .order_by(Dataset.uploaded_at.desc())
            .all()
        )

    finally:
        db.close()

def get_dataset_files(dataset_id: str):

    db = get_db()

    try:
        return (
            db.query(AudioFile)
            .filter(AudioFile.dataset_id == dataset_id)
            .order_by(AudioFile.original_filename)
            .all()
        )

    finally:
        db.close()
        
# ==========================================================
# Get Audio By ID
# ==========================================================

def get_audio_by_id(audio_id: str) -> Optional[AudioFile]:

    db = get_db()

    try:
        return (
            db.query(AudioFile)
            .filter(AudioFile.id == audio_id)
            .first()
        )

    finally:
        db.close()


# ==========================================================
# Upload Audio
# ==========================================================

def upload_audio(uploaded_file, language: str, uploaded_by: str):

    db = get_db()

    try:

        # --------------------------------------------
        # Verify ZIP
        # --------------------------------------------
        
        try:
            with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
                if zip_ref.testzip() is not None:
                    return False
        except zipfile.BadZipFile:
            return False
            
        uploaded_file.seek(0)

        # --------------------------------------------
        # Create Dataset
        # --------------------------------------------

        dataset_name = Path(uploaded_file.name).stem

        dataset = Dataset(
            name=dataset_name,
            zip_filename=uploaded_file.name,
            language=language,
            uploaded_by=uploaded_by,
            total_files=0,
            total_size=0.0,
            total_duration=0.0,
        )

        db.add(dataset)
        db.flush()

        # --------------------------------------------
        # Dataset Folder
        # --------------------------------------------

        dataset_folder = BASE_AUDIO_PATH / dataset.id
        dataset_folder.mkdir(parents=True, exist_ok=True)

        temp_zip = dataset_folder / uploaded_file.name

        with open(temp_zip, "wb") as f:
            shutil.copyfileobj(uploaded_file, f)

        # --------------------------------------------
        # Extract Files
        # --------------------------------------------

        # Extract to a temporary subdirectory so we can also parse metadata
        extraction_dir = dataset_folder / "_extracted"
        extraction_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(temp_zip, "r") as zip_ref:
            zip_ref.extractall(extraction_dir)

        # ── Strip single top-level wrapper folder ──────────────────────────
        # Many ZIPs wrap everything in one folder (e.g. telugu_68speakers_10hrs/).
        # Detect this: extraction_dir has exactly one child and it is a directory.
        # If so, use that child as the real root so relative paths are
        # audio/102104052/.../clip_0001.mp3 — not zip_name/audio/.../clip_0001.mp3.
        children = list(extraction_dir.iterdir())
        if len(children) == 1 and children[0].is_dir():
            path_root = children[0]
        else:
            path_root = extraction_dir

        # Parse metadata — pass the real root so metadata.csv is found there too
        metadata_map = parse_metadata_from_extraction(str(path_root))

        total_files = 0
        total_size = 0

        for extracted_file in path_root.rglob("*"):

            if not extracted_file.is_file():
                continue

            extension = extracted_file.suffix.lower()

            if extension not in config.SUPPORTED_AUDIO_FORMATS:
                continue

            unique_name = f"{uuid.uuid4()}{extension}"
            destination = dataset_folder / unique_name
            shutil.move(str(extracted_file), str(destination))

            size_mb = destination.stat().st_size / (1024 * 1024)

            # Full relative path from the real root, forward-slash normalised.
            original_name = str(extracted_file.relative_to(path_root)).replace("\\", "/")
            meta = metadata_map.get(original_name)
            
            if not meta:
                base_name = extracted_file.stem
                meta = metadata_map.get(base_name)
                
            if not meta and len(metadata_map) == 1 and total_files == 0:
                # If this is the very first file and there's only 1 metadata entry, we can guess it's for this file.
                # Since we don't know total_files from the zip yet (we are iterating), we just check if it's the only one in the map
                # and maybe we can just assign it if the map has 1 entry and we assume there's 1 audio file.
                meta = list(metadata_map.values())[0]
                
            if not meta:
                meta = {}


            audio = AudioFile(

                dataset_id=dataset.id,

                filename=unique_name,

                original_filename=original_name,

                file_path=str(destination),

                language=language,

                duration=0.0,

                status=AudioStatus.UNASSIGNED,

                uploaded_by=uploaded_by,

                assigned_to=None,

                original_transcript=meta.get("original_transcript"),

                english_translation=meta.get("english_translation"),

                metadata_json=meta.get("raw_metadata"),
            )

            db.add(audio)

            total_files += 1
            total_size += size_mb

        # Clean up extraction dir
        shutil.rmtree(extraction_dir, ignore_errors=True)

        # --------------------------------------------
        # Dataset Statistics
        # --------------------------------------------

        dataset.total_files = total_files
        dataset.total_size = round(total_size, 2)

        # TODO:
        # dataset.total_duration = actual_duration

        db.commit()

        temp_zip.unlink(missing_ok=True)

        return True

    except Exception:
        db.rollback()
        logger.exception("Audio upload failed")

        if 'dataset_folder' in locals() and dataset_folder.exists():
            shutil.rmtree(dataset_folder, ignore_errors=True)

        return False

    finally:

        db.close()


# ==========================================================
# Update Audio Status
# ==========================================================

def update_audio_status(audio_id: str, status: AudioStatus) -> bool:

    db = get_db()

    try:

        audio = (
            db.query(AudioFile)
            .filter(AudioFile.id == audio_id)
            .first()
        )

        if not audio:
            return False

        audio.status = status

        db.commit()

        return True

    except Exception:
        db.rollback()
        logger.exception(f"Failed to update audio status for {audio_id}")
        return False

    finally:
        db.close()


# ==========================================================
# Delete Audio
# ==========================================================

def delete_audio(audio_id: str) -> bool:

    db = get_db()

    try:

        audio = (
            db.query(AudioFile)
            .filter(AudioFile.id == audio_id)
            .first()
        )

        if not audio:
            return False

        annotations = db.query(Annotation).filter(Annotation.audio_id == audio_id).all()
        for ann in annotations:
            db.delete(ann)

        if os.path.exists(audio.file_path):
            os.remove(audio.file_path)

        db.delete(audio)
        db.commit()

        return True

    except Exception:
        db.rollback()
        logger.exception(f"Failed to delete audio {audio_id}")
        return False

    finally:
        db.close()


# ==========================================================
# Delete Dataset
# ==========================================================

def delete_dataset(dataset_id: str) -> tuple[bool, str]:
    """
    Delete an entire dataset:
    - Deletes all Annotation rows for every audio file in the dataset.
    - Deletes all AudioFile rows.
    - Deletes the Dataset row.
    - Removes the on-disk folder (uuid-named folder under BASE_AUDIO_PATH).

    Returns:
        (True, "") on success, or (False, reason) on failure.
    """
    db = get_db()

    try:
        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if not dataset:
            return False, "Dataset not found."

        audio_files = (
            db.query(AudioFile)
            .filter(AudioFile.dataset_id == dataset_id)
            .all()
        )

        # Delete all annotations for every audio file first
        for audio in audio_files:
            db.query(Annotation).filter(
                Annotation.audio_id == audio.id
            ).delete(synchronize_session=False)

        # Delete all audio file rows
        for audio in audio_files:
            db.delete(audio)

        # Delete the dataset row
        db.delete(dataset)
        db.commit()

        # Remove files from disk — dataset folder is BASE_AUDIO_PATH / dataset_id
        dataset_folder = BASE_AUDIO_PATH / dataset_id
        if dataset_folder.exists():
            shutil.rmtree(dataset_folder, ignore_errors=True)
            logger.info(f"Deleted dataset folder: {dataset_folder}")

        logger.info(
            f"Dataset {dataset_id} deleted: "
            f"{len(audio_files)} audio files removed."
        )

        return True, ""

    except Exception:
        db.rollback()
        logger.exception(f"Failed to delete dataset {dataset_id}")
        return False, "An unexpected error occurred. Check the logs."

    finally:
        db.close()


# ==========================================================
# Import Metadata for Existing Dataset
# ==========================================================

def get_csv_column_names(metadata_file) -> list:
    """
    Read only the header row of a CSV and return the column names.
    Used by the UI to let the admin map columns before importing.
    """
    import csv as _csv
    import io

    metadata_file.seek(0)
    content = metadata_file.read().decode("utf-8", errors="replace")
    metadata_file.seek(0)

    reader = _csv.DictReader(io.StringIO(content))
    return list(reader.fieldnames or [])


def import_metadata_for_dataset(
    dataset_id: str,
    metadata_file,
    filename_col: str = None,
    transcript_col: str = None,
    translation_col: str = None,
) -> tuple[int, int]:
    """
    Parse a standalone metadata.csv or metadata.json file and apply
    the transcript/translation data to AudioFile rows in an already-
    imported dataset.

    Args:
        dataset_id:      The ID of the target dataset.
        metadata_file:   A file-like object (e.g. from st.file_uploader).
        filename_col:    Column to use as the audio filename key (overrides auto-detect).
        transcript_col:  Column to use as the original transcript (overrides auto-detect).
        translation_col: Column to use as the English translation (overrides auto-detect).

    Returns:
        (matched_count, total_rows) so the caller can report coverage.
    """
    import tempfile
    from utils.metadata_parser import parse_metadata_from_file

    db = get_db()

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = os.path.join(tmp_dir, metadata_file.name)
            metadata_file.seek(0)
            with open(dest_path, "wb") as f:
                f.write(metadata_file.read())

            metadata_map = parse_metadata_from_file(
                dest_path,
                filename_col=filename_col,
                transcript_col=transcript_col,
                translation_col=translation_col,
            )

        if not metadata_map:
            return 0, 0

        files = (
            db.query(AudioFile)
            .filter(AudioFile.dataset_id == dataset_id)
            .all()
        )

        matched = 0

        for audio in files:
            meta = metadata_map.get(audio.original_filename)
            if not meta:
                base_name = os.path.splitext(os.path.basename(audio.original_filename))[0]
                meta = metadata_map.get(base_name)
                
            if not meta and len(metadata_map) == 1 and len(files) == 1:
                meta = list(metadata_map.values())[0]
                
            if meta:
                audio.original_transcript = meta.get("original_transcript")
                audio.english_translation = meta.get("english_translation")
                audio.metadata_json = meta.get("raw_metadata")
                matched += 1

        db.commit()

        logger.info(
            f"Metadata import for dataset {dataset_id}: "
            f"{matched}/{len(files)} files matched."
        )

        return matched, len(metadata_map)

    except Exception:
        db.rollback()
        logger.exception(f"Failed to import metadata for dataset {dataset_id}")
        return 0, 0

    finally:
        db.close()