import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
BEDROCK_FALLBACK_MODEL_ID = os.getenv("BEDROCK_FALLBACK_MODEL_ID", "amazon.nova-pro-v1:0")
NOVA_PRO_MODEL_ID = "amazon.nova-pro-v1:0"

AWS_CA_BUNDLE = os.getenv("AWS_CA_BUNDLE", "").strip()
REQUESTS_CA_BUNDLE = os.getenv("REQUESTS_CA_BUNDLE", "").strip()
if AWS_CA_BUNDLE:
    os.environ["AWS_CA_BUNDLE"] = AWS_CA_BUNDLE
if REQUESTS_CA_BUNDLE:
    os.environ["REQUESTS_CA_BUNDLE"] = REQUESTS_CA_BUNDLE


def print_client_error(error: ClientError) -> None:
    details = error.response.get("Error", {})
    print(f"Erro AWS: {details.get('Code', 'Unknown')}: {details.get('Message', str(error))}")


def list_models() -> None:
    print("\nModelos Amazon e Anthropic disponíveis:")
    client = boto3.client("bedrock", region_name=AWS_REGION)
    try:
        response = client.list_foundation_models()
    except ClientError as error:
        print_client_error(error)
        return

    models = response.get("modelSummaries", [])
    selected = [
        model
        for model in models
        if model.get("providerName", "").lower() in {"amazon", "anthropic"}
    ]
    if not selected:
        print("- Nenhum modelo Amazon ou Anthropic retornado.")
        return
    for model in selected:
        print(f"- {model.get('providerName')}: {model.get('modelId')}")


def test_model(model_id: str) -> None:
    print(f"\nTestando modelo: {model_id}")
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    try:
        response = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "Responda somente com: OK"}],
                }
            ],
            inferenceConfig={"maxTokens": 20, "temperature": 0.0},
        )
        answer = response["output"]["message"]["content"][0]["text"]
        print(f"Resposta: {answer}")
    except ClientError as error:
        print_client_error(error)


def main() -> None:
    print(f"AWS_REGION: {AWS_REGION}")
    print(f"BEDROCK_MODEL_ID: {BEDROCK_MODEL_ID}")
    print(f"BEDROCK_FALLBACK_MODEL_ID: {BEDROCK_FALLBACK_MODEL_ID}")
    token_status = "configurado" if os.getenv("AWS_BEARER_TOKEN_BEDROCK") else "não configurado"
    print(f"AWS_BEARER_TOKEN_BEDROCK: {token_status}")

    list_models()
    test_model(NOVA_PRO_MODEL_ID)
    if BEDROCK_MODEL_ID != NOVA_PRO_MODEL_ID:
        test_model(BEDROCK_MODEL_ID)


if __name__ == "__main__":
    main()
