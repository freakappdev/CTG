import pandas as pd
import numpy as np
import gzip
import io
import matplotlib.pyplot as plt

# Convert HEX to a cleaned int16 array (values 0 and 255 are treated as NaN)
def decode_hex_to_clean_int16(hex_data):
    cleaned = hex_data.replace("\n", "").replace(" ", "").strip()
    compressed_bytes = bytes.fromhex(cleaned)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed_bytes)) as f:
        decompressed = f.read()
    int_array = np.frombuffer(decompressed, dtype=np.int16)
    mask = (int_array != 0) & (int_array != 255)
    return np.where(mask, int_array, np.nan)

# Split into segments based on continuous NaN gaps
def find_segments_by_gap(data, min_gap_length=60):
    isnan = np.isnan(data)
    segments = []
    start = 0
    i = 0
    while i < len(data):
        if isnan[i]:
            gap_start = i
            while i < len(data) and isnan[i]:
                i += 1
            gap_length = i - gap_start
            if gap_length >= min_gap_length:
                segments.append((start, gap_start))
                start = i
        else:
            i += 1
    if start < len(data):
        segments.append((start, len(data)))
    return segments

# Read the CSV file
df = pd.read_csv("alldata.csv")

output_rows = []
sequence_id = 1

for patient_index, row in df.iterrows():
    fhr = decode_hex_to_clean_int16(row["fhr1hex"])
    ua = decode_hex_to_clean_int16(row["uahex"])
    afm = decode_hex_to_clean_int16(row["afmhex"])

    segments = find_segments_by_gap(fhr, min_gap_length=60)

    for seg_index, (start, end) in enumerate(segments, 1):
        fhr_seg = fhr[start:end]
        ua_seg = ua[start:end]
        afm_seg = afm[start:end]

        # Skip if segment is too short
        if len(fhr_seg) < 600:
            continue

        output_rows.append({
            "sequence_id": sequence_id,
            "patient_no": patient_index + 1,
            "segment_no": seg_index,
            "fhr": str(fhr_seg.tolist()),
            "ua": str(ua_seg.tolist()),
            "afm": str(afm_seg.tolist())
        })

        sequence_id += 1

# Save to Excel
df_output = pd.DataFrame(output_rows)
df_output.to_excel("alldata_segmented.xlsx", index=False)
