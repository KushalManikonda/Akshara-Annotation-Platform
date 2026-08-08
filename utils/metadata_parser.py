import csv
import json
import os
from typing import Dict, Any, Optional, List


def get_csv_columns(file_path: str) -> List[str]:
    """Return the column headers from a CSV file."""
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or [])


def parse_metadata_from_extraction(extracted_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    Looks for a metadata.csv or metadata.json in the extracted directory.
    Returns a dictionary mapping audio filename to its metadata dictionary.

    Expected CSV columns (at minimum):
    - filename / audio_filename / file / audio_file / clip / name
    - transcript / original_transcript
    - translation / english_translation

    Expected JSON structure:
    [
        {"filename": "...", "transcript": "...", "translation": "..."},
        ...
    ]
    or
    {
        "filename.wav": {"transcript": "...", "translation": "..."},
        ...
    }
    """
    metadata_map = {}

    csv_path = os.path.join(extracted_dir, "metadata.csv")
    json_path = os.path.join(extracted_dir, "metadata.json")

    if os.path.exists(csv_path):
        metadata_map = _parse_csv(csv_path)
    elif os.path.exists(json_path):
        metadata_map = _parse_json(json_path)

    from pathlib import Path
    for json_file in Path(extracted_dir).rglob("*.json"):
        if json_file.name in ["metadata.json", "metadata.csv"]:
            continue
            
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if isinstance(data, list) or isinstance(data, dict):
                base_name = json_file.stem
                for ext in [".wav", ".mp3", ".flac", ".m4a"]:
                    possible_audio = json_file.with_suffix(ext)
                    if possible_audio.exists():
                        rel_path = str(possible_audio.relative_to(Path(extracted_dir))).replace("\\", "/")
                        metadata_map[rel_path] = {
                            "original_transcript": json.dumps(data),
                            "english_translation": None,
                            "raw_metadata": "{}"
                        }
                        break
                else:
                    metadata_map[base_name] = {
                        "original_transcript": json.dumps(data),
                        "english_translation": None,
                        "raw_metadata": "{}"
                    }
        except Exception:
            pass

    return metadata_map


def parse_metadata_from_file(
    file_path: str,
    filename_col: Optional[str] = None,
    transcript_col: Optional[str] = None,
    translation_col: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Parse a standalone metadata file with explicit column name overrides.

    Args:
        file_path: Absolute path to the CSV or JSON file.
        filename_col: Column to use as the audio filename key.
        transcript_col: Column to use as the original transcript.
        translation_col: Column to use as the English translation.

    Returns:
        Dict mapping audio filename → metadata dict.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        return _parse_csv(
            file_path,
            filename_col=filename_col,
            transcript_col=transcript_col,
            translation_col=translation_col,
        )
    elif ext == ".json":
        return _parse_json(file_path)

    return {}


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

_FILENAME_ALIASES = [
    "filename", "audio_filename", "file", "audio_file",
    "clip", "clip_id", "name", "audio", "audio_name",
]

_TRANSCRIPT_ALIASES = [
    "transcript", "original_transcript", "text", "original_text",
    "source", "utterance",
]

_TRANSLATION_ALIASES = [
    "translation", "english_translation", "english", "target",
    "translated_text",
]


def _find_col(keys: List[str], aliases: List[str]) -> Optional[str]:
    """Find the first column whose name matches any alias (case-insensitive)."""
    lower_keys = {k.lower(): k for k in keys}
    for alias in aliases:
        if alias in lower_keys:
            return lower_keys[alias]
    # Fallback: any column that *contains* the first alias word
    primary = aliases[0]
    for orig in keys:
        if primary in orig.lower():
            return orig
    return None


def _parse_csv(
    path: str,
    filename_col: Optional[str] = None,
    transcript_col: Optional[str] = None,
    translation_col: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    metadata_map = {}

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        keys = list(reader.fieldnames or [])

        # Resolve columns — explicit override wins, then auto-detect
        fn_key   = filename_col    or _find_col(keys, _FILENAME_ALIASES)
        tr_key   = transcript_col  or _find_col(keys, _TRANSCRIPT_ALIASES)
        tran_key = translation_col or _find_col(keys, _TRANSLATION_ALIASES)

        if not fn_key:
            return {}

        for row in reader:
            raw_filename = row.get(fn_key, "").strip()
            if not raw_filename:
                continue

            # Normalise path separators (Windows backslash → forward slash).
            # Do NOT strip to basename: many datasets have hundreds of files
            # with the same filename in different subdirectories, so the full
            # relative path is the only reliable unique key.
            filename = raw_filename.replace("\\", "/")

            extra_data = dict(row)
            if fn_key in extra_data:
                del extra_data[fn_key]
            if tr_key and tr_key in extra_data:
                del extra_data[tr_key]
            if tran_key and tran_key in extra_data:
                del extra_data[tran_key]
            
            metadata_map[filename] = {
                "original_transcript": row.get(tr_key) if tr_key else None,
                "english_translation": row.get(tran_key) if tran_key else None,
                "raw_metadata": json.dumps(extra_data) if extra_data else "{}",
            }

    return metadata_map


def _parse_json(path: str) -> Dict[str, Dict[str, Any]]:
    metadata_map = {}

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0 and not any(k in data[0] for k in ["filename", "audio_filename", "file"]):
                base_name = os.path.splitext(os.path.basename(path))[0]
                metadata_map[base_name] = {
                    "original_transcript": json.dumps(data),
                    "english_translation": None,
                    "raw_metadata": "{}"
                }
                return metadata_map
                
            if isinstance(data, list):
                for item in data:
                    filename = (
                        item.get("filename")
                        or item.get("audio_filename")
                        or item.get("file")
                    )
                    if not filename:
                        continue
                    metadata_map[filename.replace("\\", "/")] = _extract_json_item(item)
            elif isinstance(data, dict):
                if data and not any(k in data for k in ["filename", "audio_filename", "file"]) and "start" in data:
                     base_name = os.path.splitext(os.path.basename(path))[0]
                     metadata_map[base_name] = {
                         "original_transcript": json.dumps([data]),
                         "english_translation": None,
                         "raw_metadata": "{}"
                     }
                     return metadata_map
                     
                for filename, item in data.items():
                    if isinstance(item, dict):
                        metadata_map[filename.replace("\\", "/")] = _extract_json_item(item)
        except json.JSONDecodeError:
            pass

    return metadata_map


def _extract_json_item(item: Dict[str, Any]) -> Dict[str, Any]:
    extra_data = dict(item)
    for k in ["filename", "audio_filename", "file", "transcript", "original_transcript", "translation", "english_translation"]:
        if k in extra_data:
            del extra_data[k]
            
    return {
        "original_transcript": item.get("transcript") or item.get("original_transcript"),
        "english_translation": item.get("translation") or item.get("english_translation"),
        "raw_metadata": json.dumps(extra_data) if extra_data else "{}",
    }
