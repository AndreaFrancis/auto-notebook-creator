import os
import json


def replace_wildcards(
    templates, wildcards, replacements, has_numeric_columns, has_categoric_columns
):
    if len(wildcards) != len(replacements):
        raise ValueError(
            "The number of wildcards must match the number of replacements."
        )

    new_templates = []
    for tmp in templates:
        if "type" in tmp and tmp["type"] == "numeric" and not has_numeric_columns:
            continue
        if "type" in tmp and tmp["type"] == "categoric" and not has_categoric_columns:
            continue
        tmp_text = tmp["source"].strip()
        for wildcard, replacement in zip(wildcards, replacements):
            tmp_text = tmp_text.replace(wildcard, replacement)
        new_templates.append({"cell_type": tmp["cell_type"], "source": tmp_text})

    return new_templates


def load_json_files_from_folder(folder_path):
    components = {}

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, "r") as json_file:
                data = json.load(json_file)
                components[data["notebook_title"]] = data

    return components
