"""Arabic dataset configurations."""

DATASETS_AR = [
    {
        "name": "HPLT/HPLT2.0_cleaned",
        "subset": "ara_Arab",
        "text_key": "text",
        "output_name": "hplt2",
    },
    {
        "name": "uonlp/CulturaX",
        "subset": "ar",
        "text_key": "text",
        "output_name": "culturax",
    },
    {
        "name": "lightonai/ArabicWeb24",
        "subset": None,
        "text_key": "text",
        "output_name": "arabicweb24",
    },
    {
        "name": "ClusterlabAi/101_billion_arabic_words_dataset",
        "subset": None,
        "text_key": "text",
        "output_name": "clusterlab",
    },
    {
        "name": "allenai/c4",
        "subset": "ar",
        "text_key": "text",
        "output_name": "c4_ar",
    },
    {
        "name": "HuggingFaceFW/fineweb-2",
        "subset": "arb_Arab",
        "text_key": "text",
        "output_name": "fineweb2",
    },
    {
        "name": "HuggingFaceFW/finepdfs",
        "subset": "arb_Arab",
        "text_key": "text",
        "output_name": "finepdfs",
    },
]
