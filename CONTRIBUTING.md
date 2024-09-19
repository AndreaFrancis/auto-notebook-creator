# How to contribute

Thanks for your interest in contributing! 🙌 This project helps users quickly create notebooks to showcase how they use datasets. The generated code can be added to their repositories or used in research projects.

## Ways to Contribute
There are a few ways you can help:

- 💡**Share ideas**: Got a cool feature in mind? Let us know!
- 🐞**Report bugs**: If something isn’t working, we’d love to fix it.
- 🚀**Suggest improvements**: Any suggestions to make the tool better are welcome.
- 📓**Add new notebook types**: This is one of the most exciting ways to contribute!

## For Ideas, Bugs, or Suggestions:
- Start a new discussion [here](https://huggingface.co/spaces/asoria/auto-notebook-creator/discussions/new).
- Tell me what’s on your mind and include any details that might help.

## For Adding New Notebook Types:
- Open a pull request (PR) [here](https://huggingface.co/spaces/asoria/auto-notebook-creator/discussions?new_pr=true).
- Add a new `.json` file in the notebooks folder. There’s a sample file you can copy and tweak.
- Submit your PR! 🎉

## Running the Space Application
To execute the space, follow these steps:

1. Set Required Environment Variables:
- `NOTEBOOKS_REPOSITORY`: The name of the repository where the generated notebooks will be stored. Ensure that you have **write** permissions for this repository. For example, I use [asoria/dataset-notebook-creator-content](https://huggingface.co/datasets/asoria/dataset-notebook-creator-content) repository.
- `HF_TOKEN`: Your Hugging Face token, used for authentication to push changes to the repository.

Example setup:

```bash
export HF_TOKEN=your_huggingface_token
export NOTEBOOKS_REPOSITORY=your_repository_name
```

2. Execute the following command to start the application:

```bash
python app.py
```

I am excited to see what you come up with. Thanks for helping make this project even better! 💖

