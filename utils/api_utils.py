from httpx import Client

BASE_DATASETS_SERVER_URL = "https://datasets-server.huggingface.co"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

client = Client(headers=HEADERS)


def get_compatible_libraries(dataset: str):
    response = client.get(
        f"{BASE_DATASETS_SERVER_URL}/compatible-libraries?dataset={dataset}"
    )
    response.raise_for_status()
    return response.json()


def get_first_rows(dataset: str, config: str, split: str):
    resp = client.get(
        f"{BASE_DATASETS_SERVER_URL}/first-rows?dataset={dataset}&config={config}&split={split}"
    )
    resp.raise_for_status()
    content = resp.json()
    rows = content["rows"]
    return [row["row"] for row in rows]


def get_splits(dataset: str, config: str):
    resp = client.get(
        f"{BASE_DATASETS_SERVER_URL}/splits?dataset={dataset}&config={config}"
    )
    resp.raise_for_status()
    content = resp.json()
    return content["splits"]
