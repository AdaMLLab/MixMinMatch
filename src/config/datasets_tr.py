"""Turkish dataset configurations."""

DATASETS_TR = [
    {
        "name": "HPLT/HPLT2.0_cleaned",
        "subset": "tur_Latn_1",  # Note: folder is tur_Latn_1, not tur_Latn
        "text_key": "text",
        "output_name": "hplt2",
        # Download: huggingface-cli download HPLT/HPLT2.0_cleaned --include "*tur*" --local-dir ./data/tr/downloads/hplt2
    },
    {
        "name": "HuggingFaceFW/fineweb-2",
        "subset": "tur_Latn",
        "text_key": "text",
        "output_name": "fineweb2",
        # Download: huggingface-cli download HuggingFaceFW/fineweb-2 --include "data/tur_Latn/*" --local-dir ./data/tr/downloads/fineweb2
    },
    {
        "name": "uonlp/CulturaX",
        "subset": "tr",
        "text_key": "text",
        "output_name": "culturax",
        # Download: huggingface-cli download uonlp/CulturaX --include "tr/*" --local-dir ./data/tr/downloads/culturax
    },
    {
        "name": "allenai/c4",
        "subset": "tr",
        "text_key": "text",
        "output_name": "c4_tr",
        # Download: huggingface-cli download allenai/c4 --include "multilingual/c4-tr*" --local-dir ./data/tr/downloads/c4
    },
    {
        "name": "vngrs-ai/vngrs-web-corpus",
        "subset": None,  # Turkish-only dataset
        "text_key": "text",
        "output_name": "vngrs",
        # Download: huggingface-cli download vngrs-ai/vngrs-web-corpus --local-dir ./data/tr/downloads/vngrs
    },
]

# HuggingFace CLI download commands for Turkish
DOWNLOAD_COMMANDS_TR = [
    "huggingface-cli download HPLT/HPLT2.0_cleaned --include '*tur*' --local-dir ./data/tr/downloads/hplt2",
    "huggingface-cli download HuggingFaceFW/fineweb-2 --include 'data/tur_Latn/*' --local-dir ./data/tr/downloads/fineweb2",
    "huggingface-cli download uonlp/CulturaX --include 'tr/*' --local-dir ./data/tr/downloads/culturax",
    "huggingface-cli download allenai/c4 --include 'multilingual/c4-tr*' --local-dir ./data/tr/downloads/c4",
    "huggingface-cli download vngrs-ai/vngrs-web-corpus --local-dir ./data/tr/downloads/vngrs",
]
