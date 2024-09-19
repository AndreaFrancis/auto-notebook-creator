import gradio as gr
from gradio_huggingfacehub_search import HuggingfaceHubSearch
import nbformat as nbf
from huggingface_hub import HfApi
import logging
from utils.notebook_utils import (
    replace_wildcards,
    load_json_files_from_folder,
)
from utils.api_utils import get_compatible_libraries, get_first_rows, get_splits
from dotenv import load_dotenv
import os
from nbconvert import HTMLExporter
import uuid
import pandas as pd

load_dotenv()

URL = "https://huggingface.co/spaces/asoria/auto-notebook-creator"

HF_TOKEN = os.getenv("HF_TOKEN")
assert HF_TOKEN is not None, "You need to set HF_TOKEN in your environment variables"

NOTEBOOKS_REPOSITORY = os.getenv("NOTEBOOKS_REPOSITORY")
assert (
    NOTEBOOKS_REPOSITORY is not None
), "You need to set NOTEBOOKS_REPOSITORY in your environment variables"


logging.basicConfig(level=logging.INFO)

# TODO: Validate notebook templates format
folder_path = "notebooks"
notebook_templates = load_json_files_from_folder(folder_path)
logging.info(f"Available notebooks {notebook_templates.keys()}")


def create_notebook_file(cells, notebook_name):
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_code_cell(
            cmd["source"]
            if isinstance(cmd["source"], str)
            else "\n".join(cmd["source"])
        )
        if cmd["cell_type"] == "code"
        else nbf.v4.new_markdown_cell(cmd["source"])
        for cmd in cells
    ]

    with open(notebook_name, "w") as f:
        nbf.write(nb, f)
    logging.info(f"Notebook {notebook_name} created successfully")
    html_exporter = HTMLExporter()
    html_data, _ = html_exporter.from_notebook_node(nb)
    return html_data


def longest_string_column(df):
    longest_col = None
    max_length = 0

    for col in df.select_dtypes(include=["object", "string"]):
        max_col_length = df[col].str.len().max()
        if max_col_length > max_length:
            max_length = max_col_length
            longest_col = col

    return longest_col


def _push_to_hub(
    dataset_id,
    notebook_file,
):
    logging.info(f"Pushing notebook to hub: {dataset_id} on file {notebook_file}")

    notebook_name = notebook_file.split("/")[-1]
    api = HfApi(token=HF_TOKEN)
    try:
        logging.info(f"About to push {notebook_file} - {dataset_id}")
        api.upload_file(
            path_or_fileobj=notebook_file,
            path_in_repo=notebook_name,
            repo_id=NOTEBOOKS_REPOSITORY,
            repo_type="dataset",
        )
    except Exception as e:
        logging.info("Failed to push notebook", e)
        raise


def generate_cells(dataset_id, notebook_title):
    logging.info(f"Generating {notebook_title} notebook for dataset {dataset_id}")
    cells = notebook_templates[notebook_title]["notebook_template"]
    notebook_type = notebook_templates[notebook_title]["notebook_type"]
    dataset_types = notebook_templates[notebook_title]["dataset_types"]
    compatible_library = notebook_templates[notebook_title]["compatible_library"]
    try:
        libraries = get_compatible_libraries(dataset_id)
        if not libraries:
            logging.error(
                f"Dataset not compatible with any loading library (pandas/datasets)"
            )
            return (
                "",
                "## ❌ This dataset is not compatible with pandas or datasets libraries ❌",
            )

        library_code = next(
            (
                lib
                for lib in libraries.get("libraries", [])
                if lib["library"] == compatible_library
            ),
            None,
        )
        if not library_code:
            logging.error(f"Dataset not compatible with {compatible_library} library")
            return (
                "",
                f"## ❌ This dataset is not compatible with '{compatible_library}' library ❌",
            )
        first_config_loading_code = library_code["loading_codes"][0]
        first_code = first_config_loading_code["code"]
        first_config = first_config_loading_code["config_name"]
        first_split = get_splits(dataset_id, first_config)[0]["split"]
        first_rows = get_first_rows(dataset_id, first_config, first_split)
    except Exception as err:
        gr.Error("Unable to retrieve dataset info from HF Hub.")
        logging.error(f"Failed to fetch compatible libraries: {err}")
        return "", f"## ❌ This dataset is not accessible from the Hub {err}❌"

    df = pd.DataFrame.from_dict(first_rows).sample(frac=1).head(3)

    longest_col = longest_string_column(df)
    html_code = f"<iframe src='https://huggingface.co/datasets/{dataset_id}/embed/viewer' width='80%' height='560px'></iframe>"
    wildcards = [
        "{dataset_name}",
        "{first_code}",
        "{html_code}",
        "{longest_col}",
        "{first_config}",
        "{first_split}",
    ]
    replacements = [
        dataset_id,
        first_code,
        html_code,
        longest_col,
        first_config,
        first_split,
    ]
    has_numeric_columns = len(df.select_dtypes(include=["number"]).columns) > 0
    has_categoric_columns = len(df.select_dtypes(include=["object"]).columns) > 0

    valid_dataset = False
    if "text" in dataset_types and has_categoric_columns:
        valid_dataset = True
    if "numeric" in dataset_types and has_numeric_columns:
        valid_dataset = True
    if not valid_dataset:
        logging.error(
            f"Dataset does not have the column types needed for this notebook which expects to have {dataset_types} data types."
        )
        return (
            "",
            f"## ❌ This dataset does not have {dataset_types} columns, which are required for this notebook type ❌",
        )

    cells = replace_wildcards(
        cells, wildcards, replacements, has_numeric_columns, has_categoric_columns
    )

    notebook_name = (
        f"{dataset_id.replace('/', '-')}-{notebook_type}-{uuid.uuid4()}.ipynb"
    )
    html_content = create_notebook_file(cells, notebook_name=notebook_name)
    _push_to_hub(dataset_id, notebook_name)
    notebook_link = f"https://colab.research.google.com/#fileId=https%3A//huggingface.co/datasets/{NOTEBOOKS_REPOSITORY}/blob/main/{notebook_name}"
    return (
        html_content,
        f"[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)]({notebook_link})",
    )


css = """
.prose :where(pre):not(:where([class~=not-prose],[class~=not-prose] *)) {
    background-color: var(--table-even-background-fill);  /* Fix dark mode */
}
"""

with gr.Blocks(css=css) as demo:
    gr.Markdown("# 🤖 Dataset notebook creator 🕵️")
    gr.Markdown(
        f"[![Notebooks: {len(notebook_templates)}](https://img.shields.io/badge/Notebooks-{len(notebook_templates)}-blue.svg)]({URL}/tree/main/notebooks)"
    )
    gr.Markdown(
        f"[![Contribute a Notebook](https://img.shields.io/badge/Contribute%20a%20Notebook-8A2BE2)]({URL}/blob/main/CONTRIBUTING.md)"
    )
    text_input = gr.Textbox(label="Suggested notebook type", visible=False)

    gr.Markdown("## 1. Select a dataset from Huggingface Hub")
    dataset_name = HuggingfaceHubSearch(
        label="Hub Dataset ID",
        placeholder="Search for dataset id on Huggingface",
        search_type="dataset",
        value="",
    )

    dataset_samples = gr.Examples(
        examples=[
            [
                "scikit-learn/iris",
                "Try this dataset for Exploratory Data Analysis (EDA)",
            ],
            [
                "infinite-dataset-hub/GlobaleCuisineRecipes",
                "Try this dataset for Text Embeddings",
            ],
            [
                "infinite-dataset-hub/GlobalBestSellersSummaries",
                "Try this dataset for Retrieval-augmented generation (RAG)",
            ],
            [
                "asoria/english-quotes-text",
                "Try this dataset for Supervised fine-tuning (SFT)",
            ],
        ],
        inputs=[dataset_name, text_input],
        cache_examples=False,
    )

    gr.Markdown("## 2. Preview the dataset")

    @gr.render(inputs=dataset_name)
    def embed(name):
        if not name:
            return gr.Markdown("### No dataset provided")
        html_code = f"""
                    <iframe
                    src="https://huggingface.co/datasets/{name}/embed/viewer/default/train"
                    frameborder="0"
                    width="100%"
                    height="350px"
                    ></iframe>
                    """
        return gr.HTML(value=html_code, elem_classes="viewer")

    gr.Markdown("## 3. Select the type of notebook you want to generate")
    notebook_type = gr.Dropdown(
        choices=notebook_templates.keys(),
        label="Notebook type",
        value="Text Embeddings",
    )
    generate_button = gr.Button("Generate Notebook", variant="primary")

    gr.Markdown("## 4. Notebook result + Open in Colab")
    go_to_notebook = gr.Markdown()
    code_component = gr.HTML()

    generate_button.click(
        generate_cells,
        inputs=[dataset_name, notebook_type],
        outputs=[code_component, go_to_notebook],
    )

    gr.Markdown(
        "🚧 Note: Some code may not be compatible with datasets that contain binary data or complex structures. 🚧"
    )

demo.launch()
