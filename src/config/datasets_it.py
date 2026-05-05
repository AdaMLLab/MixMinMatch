"""Italian dataset configurations."""

DATASETS_IT = [
    {
        "name": "HPLT/HPLT2.0_cleaned",
        "subset": "ita_Latn",
        "text_key": "text",
        "output_name": "hplt2",
        # Download: huggingface-cli download HPLT/HPLT2.0_cleaned --include "ita_Latn*/*" --local-dir ./data/it/downloads/hplt2
    },
    {
        "name": "HuggingFaceFW/fineweb-2",
        "subset": "ita_Latn",
        "text_key": "text",
        "output_name": "fineweb2",
        # Download: huggingface-cli download HuggingFaceFW/fineweb-2 --include "data/ita_Latn/*" --local-dir ./data/it/downloads/fineweb2
    },
    {
        "name": "uonlp/CulturaX",
        "subset": "it",
        "text_key": "text",
        "output_name": "culturax",
        # Download: huggingface-cli download uonlp/CulturaX --include "it/*" --local-dir ./data/it/downloads/culturax
    },
    {
        "name": "allenai/c4",
        "subset": "it",
        "text_key": "text",
        "output_name": "c4",
        # Download: huggingface-cli download allenai/c4 --include "multilingual/c4-it*" --local-dir ./data/it/downloads/c4
    },
]

# HuggingFace CLI download commands for Italian
DOWNLOAD_COMMANDS_IT = [
    "huggingface-cli download HPLT/HPLT2.0_cleaned --include 'ita_Latn*/*' --local-dir ./data/it/downloads/hplt2 --repo-type dataset",
    "huggingface-cli download HuggingFaceFW/fineweb-2 --include 'data/ita_Latn/*' --local-dir ./data/it/downloads/fineweb2 --repo-type dataset",
    "huggingface-cli download uonlp/CulturaX --include 'it/*' --local-dir ./data/it/downloads/culturax --repo-type dataset",
    "huggingface-cli download allenai/c4 --include 'multilingual/c4-it*' --local-dir ./data/it/downloads/c4 --repo-type dataset",
]
