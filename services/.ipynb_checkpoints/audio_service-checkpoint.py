import os
import shutil
import uuid
import zipfile

from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from database.database import SessionLocal
from database.models import AudioFile, Dataset
from database.enums import AudioStatus

# ==========================================================
# Storage
# ==========================================================

BASE_AUDIO_PATH = Path("assets/audio")

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

        total_files = 0
        total_size = 0

        with zipfile.ZipFile(temp_zip, "r") as zip_ref:

            for member in zip_ref.infolist():

                if member.is_dir():
                    continue

                extension = Path(member.filename).suffix.lower()

                if extension not in [".wav", ".mp3", ".flac"]:
                    continue

                unique_name = f"{uuid.uuid4()}{extension}"

                destination = dataset_folder / unique_name

                with zip_ref.open(member) as source:
                    with open(destination, "wb") as target:
                        shutil.copyfileobj(source, target)

                size_mb = destination.stat().st_size / (1024 * 1024)

                audio = AudioFile(

                    dataset_id=dataset.id,

                    filename=unique_name,

                    original_filename=Path(member.filename).name,

                    file_path=str(destination),

                    language=language,

                    duration=0.0,

                    status=AudioStatus.UNASSIGNED,

                    uploaded_by=uploaded_by,

                    assigned_to=None,
                )

                db.add(audio)

                total_files += 1
                total_size += size_mb

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

    except Exception as e:

        db.rollback()

        print(e)

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

        if os.path.exists(audio.file_path):
            os.remove(audio.file_path)

        db.delete(audio)
        db.commit()

        return True

    finally:
        db.close()