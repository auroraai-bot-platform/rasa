import requests
import yaml

server = "http://localhost:5005"

def read(path):
    with open(path) as f:
        return f.read()

def read_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def train():
    endpoint = f"{server}/model/train"

    body = read_yaml('data.yml')

    headers = {
        "Content-Type": "application/x-yaml"
    }
    # print(body)
    response = requests.post(endpoint, headers=headers, data=yaml.dump(body))
    # print(response)
    # if response.ok:
    #     print("Writing response.out")
        # with open('response.tar.gz', 'wb') as f:
        #     f.write(response.content)
    return response

# print(body)
train()