"""Hindi dataset configurations."""

DATASETS_HI = [
    {
        "name": "HPLT/HPLT2.0_cleaned",
        "subset": "hin_Deva",
        "text_key": "text",
        "output_name": "hplt2",
        # Download: huggingface-cli download HPLT/HPLT2.0_cleaned --include "hin_Deva/*" --local-dir ./data/hi/downloads/hplt2
    },
    {
        "name": "HuggingFaceFW/fineweb-2",
        "subset": "hin_Deva",
        "text_key": "text",
        "output_name": "fineweb2",
        # Download: huggingface-cli download HuggingFaceFW/fineweb-2 --include "data/hin_Deva/*" --local-dir ./data/hi/downloads/fineweb2
    },
    {
        "name": "uonlp/CulturaX",
        "subset": "hi",
        "text_key": "text",
        "output_name": "culturax",
        # Download: huggingface-cli download uonlp/CulturaX --include "hi/*" --local-dir ./data/hi/downloads/culturax
    },
    {
        "name": "allenai/c4",
        "subset": "hi",
        "text_key": "text",
        "output_name": "c4_hi",
        # Download: huggingface-cli download allenai/c4 --include "multilingual/c4-hi*" --local-dir ./data/hi/downloads/c4
    },
    # Sangraha - SPECIAL HANDLING REQUIRED
    # Hindi is a SPLIT, not a subset. Must download with --include and load from local.
    {
        "name": "ai4bharat/sangraha",
        "subset": "verified/hin",  # Special: load from local after download
        "text_key": "text",
        "output_name": "sangraha_verified",
        "special_handling": "sangraha",  # Flag for special download handling
        # Download: huggingface-cli download ai4bharat/sangraha --include "verified/hin/*" --local-dir ./data/hi/downloads/sangraha/verified
    },
    {
        "name": "ai4bharat/sangraha",
        "subset": "unverified/hin",  # Special: load from local after download
        "text_key": "text",
        "output_name": "sangraha_unverified",
        "special_handling": "sangraha",  # Flag for special download handling
        # Download: huggingface-cli download ai4bharat/sangraha --include "unverified/hin/*" --local-dir ./data/hi/downloads/sangraha/unverified
    },
]

# HuggingFace CLI download commands for Hindi
# NOTE: Sangraha requires special handling - Hindi is a SPLIT not a subset
# If you try to use load_dataset() directly, it will download ALL languages!
DOWNLOAD_COMMANDS_HI = [
    "huggingface-cli download HPLT/HPLT2.0_cleaned --include 'hin_Deva/*' --local-dir ./data/hi/downloads/hplt2",
    "huggingface-cli download HuggingFaceFW/fineweb-2 --include 'data/hin_Deva/*' --local-dir ./data/hi/downloads/fineweb2",
    "huggingface-cli download uonlp/CulturaX --include 'hi/*' --local-dir ./data/hi/downloads/culturax",
    "huggingface-cli download allenai/c4 --include 'multilingual/c4-hi*' --local-dir ./data/hi/downloads/c4",
    # Sangraha - SPECIAL: Download only Hindi files using --include
    "huggingface-cli download ai4bharat/sangraha --include 'verified/hin/*' --local-dir ./data/hi/downloads/sangraha/verified",
    "huggingface-cli download ai4bharat/sangraha --include 'unverified/hin/*' --local-dir ./data/hi/downloads/sangraha/unverified",
]

# How to load Sangraha after downloading locally:
# DO NOT use: load_dataset("ai4bharat/sangraha", ...)
# INSTEAD use: load_dataset("parquet", data_dir="./data/hi/downloads/sangraha/verified")
