"""Thai dataset configurations."""

DATASETS_TH = [
    {
        "name": "HPLT/HPLT2.0_cleaned",
        "subset": "tha_Thai",
        "text_key": "text",
        "output_name": "hplt2",
        # Download: huggingface-cli download HPLT/HPLT2.0_cleaned --include "tha_Thai/*" --local-dir ./data/th/downloads/hplt2
    },
    {
        "name": "HuggingFaceFW/fineweb-2",
        "subset": "tha_Thai",
        "text_key": "text",
        "output_name": "fineweb2",
        # Download: huggingface-cli download HuggingFaceFW/fineweb-2 --include "data/tha_Thai/*" --local-dir ./data/th/downloads/fineweb2
    },
    {
        "name": "uonlp/CulturaX",
        "subset": "th",
        "text_key": "text",
        "output_name": "culturax",
        # Download: huggingface-cli download uonlp/CulturaX --include "th/*" --local-dir ./data/th/downloads/culturax
    },
    {
        "name": "allenai/c4",
        "subset": "th",
        "text_key": "text",
        "output_name": "c4_th",
        # Download: huggingface-cli download allenai/c4 --include "multilingual/c4-th*" --local-dir ./data/th/downloads/c4
    },
    {
        "name": "sailor2/sea-commoncrawl",
        "subset": "thai",
        "text_key": "text",
        "output_name": "sea_cc",
        "special_handling": "sea_cc",
        # Download: huggingface-cli download sailor2/sea-commoncrawl --include "thai/*" --local-dir ./data/th/downloads/sea_cc
    },
]

# HuggingFace CLI download commands for Thai
DOWNLOAD_COMMANDS_TH = [
    "huggingface-cli download HPLT/HPLT2.0_cleaned --include 'tha_Thai/*' --local-dir ./data/th/downloads/hplt2",
    "huggingface-cli download HuggingFaceFW/fineweb-2 --include 'data/tha_Thai/*' --local-dir ./data/th/downloads/fineweb2",
    "huggingface-cli download uonlp/CulturaX --include 'th/*' --local-dir ./data/th/downloads/culturax",
    "huggingface-cli download allenai/c4 --include 'multilingual/c4-th*' --local-dir ./data/th/downloads/c4",
    "huggingface-cli download sailor2/sea-commoncrawl --include 'thai/*' --local-dir ./data/th/downloads/sea_cc",
]
