# Hyun Project

여기서는 Streamlit과 Knowledge Base를 이용하여 strands agent 기반의 chatbot을 구현합니다. 전체적인 architecture는 아래와 같습니다. MCP server로 Knowledge Base, Code Interpreter를 이용하고 strands agent를 이용해 관련된 문서를 조회하여 답변을 구하고 필요하다면 다이어그램을 그래서 이해를 돕습니다. 여기서 생성된 agent는 streamlit을 이용해 UI를 제공하고 ALB와 CloudFront를 이용하여 안전하게 활용할 수 있습니다.

<img width="700" alt="image" src="https://github.com/user-attachments/assets/4d666a04-f100-45c8-8d18-3e84fdc93cf8" />

## 주요 구현

### Strands Agent

[agent.py](./application/agent.py)와 같이 app에서 agent를 실행하면 아래와 같이 run_agent가 실행됩니다. 이때 최초 실행이 되면 아래와 같이 initialize_agent()로 agent를 생성합니다. mcp_client가 준비가 되면 아래와 같이 agent를 [stream_async](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/streaming/async-iterators/)을 이용해 실행됩니다. Strands agent는 하나의 입력을 multi-step reasoning을 통해 답을 찾아가므로 중간의 출력들을 아래와 같이 show_streams으로 보여줍니다. 

```python
async def run_agent(query: str, containers):
    global index, status_msg
    global agent, mcp_client, tool_list
    
    if agent is None:
        agent, mcp_client, tool_list = initialize_agent()

    with mcp_client as client:
        agent_stream = agent.stream_async(query)
        result = await show_streams(agent_stream, containers)
    return result
```

[mcp.json](./application/mcp.json)에서는 MCP 서버에 대한 정보를 가지고 있습니다. 이 정보를 이용하여 MCPClient를 생성할 수 있습니다. mcp.json의 MCP 서버의 정보인 command, args, env를 이용해 [StdioServerParameters](https://github.com/strands-agents/sdk-python?tab=readme-ov-file#mcp-support)를 구성합니다.

```python
def create_mcp_client(mcp_server_name: str):
    config = load_mcp_config()
    mcp_servers = config["mcpServers"]
    
    mcp_client = None
    for server_name, server_config in mcp_servers.items():
        env = server_config["env"] if "env" in server_config else None

        if server_name == mcp_server_name:
            mcp_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command=server_config["command"], 
                    args=server_config["args"], 
                    env=env
                )
            ))
            break
    
    return mcp_client
```

아래와 같이 "knowledge_base"를 사용하는 MCP agent를 아래와 같이 create_mcp_client로 생성합니다. 또한 [list_tools_sync](https://github.com/strands-agents/sdk-python?tab=readme-ov-file#mcp-support)를 이용해 tool에 대한 정보를 가져와서 tools에 추가합니다. 이후 아래와 같이 agent를 생성합니다.

```python
def initialize_agent():
    """Initialize the global agent with MCP client"""
    mcp_client = create_mcp_client("knowledge_base")
        
    # Create agent within MCP client context manager
    with mcp_client as client:
        mcp_tools = client.list_tools_sync()        
        tools = []
        tools.extend(mcp_tools)
        tool_list = get_tool_list(tools)    
        system_prompt = (
            "당신의 이름은 현민이고, 질문에 대해 친절하게 답변하는 사려깊은 인공지능 도우미입니다."
            "상황에 맞는 구체적인 세부 정보를 충분히 제공합니다." 
            "모르는 질문을 받으면 솔직히 모른다고 말합니다."
        )
        model = get_model()
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            conversation_manager=conversation_manager
        )
    
    return agent, mcp_client, tool_list
```

여러개의 MCP 서버를 사용할 경우에는 [multi_mcp_agent.py](./application/multi_mcp_agent.py)을 참조합니다. 여기에서는 아래와 같이 knowledge_base_mcp_client와 repl_coder_client를 이용해 mcp client를 생성하고 mcp_tools를 extend해서 활용하여야 합니다. 

```python
def initialize_agent():
    """Initialize the global agent with MCP client"""
    knowledge_base_mcp_client = create_mcp_client("knowledge_base")
    repl_coder_client = create_mcp_client("repl_coder")
        
    # Create agent within MCP client context manager
    with knowledge_base_mcp_client, repl_coder_client:
        mcp_tools = knowledge_base_mcp_client.list_tools_sync()
        mcp_tools.extend(repl_coder_client.list_tools_sync())
```        

### MCP Servers

[mcp_retrieve.py]에서는 Knowledge Base로부터 관련된 문서를 조회합니다. bedrock-agent-runtime로 client를 정의하고 retrieve를 이용해 질문과 관련된 문서를 조회합니다. 얻어진 문서에서 text와 url과 같은 정보를 추출합니다.

```python
bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime", region_name=bedrock_region)

def retrieve(query):
    response = bedrock_agent_runtime_client.retrieve(
        retrievalQuery={"text": query},
        knowledgeBaseId=knowledge_base_id,
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": number_of_results},
            },
        )
    retrieval_results = response.get("retrievalResults", [])
    json_docs = []
    for result in retrieval_results:
        text = url = name = None
        if "content" in result:
            content = result["content"]
            if "text" in content:
                text = content["text"]

        if "location" in result:
            location = result["location"]
            if "s3Location" in location:
                uri = location["s3Location"]["uri"] if location["s3Location"]["uri"] is not None else ""
                
                name = uri.split("/")[-1]
                url = uri # TODO: add path and doc_prefix
                
            elif "webLocation" in location:
                url = location["webLocation"]["url"] if location["webLocation"]["url"] is not None else ""
                name = "WEB"

        json_docs.append({
            "contents": text,              
            "reference": {
                "url": url,                   
                "title": name,
                "from": "RAG"
            }
        })
```

[mcp_server_retrieve.py](./application/mcp_server_retrieve.py)에서는 아래와 같이 FastMCP를 이용해 Knowledge Base를 조회하는 MCP 기능을 구현합니다. 이때 retrieve라는 tool을 아래와 같이 정의할 수 있고 agent은 docstring을 참조하여 적절한 tool을 선택합니다. 


```python
from mcp.server.fastmcp import FastMCP 

mcp = FastMCP(
    name = "mcp-retrieve",
    instructions=(
        "You are a helpful assistant. "
        "You retrieve documents in RAG."
    ),
)

@mcp.tool()
def retrieve(keyword: str) -> str:
    """
    Query the keyword using RAG based on the knowledge base.
    keyword: the keyword to query
    return: the result of query
    """
    return mcp_retrieve.retrieve(keyword)

if __name__ =="__main__":
    print(f"###### main ######")
    mcp.run(transport="stdio")
```




### Knowledge Base 수동으로 생성하는 방법

[Knowledge Base](https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/knowledge-bases)에 접속해서 [Create]를 선택하여 RAG를 생성합니다. 완료가 되면 Knowledge Base의 ID를 확인합니다.

Amazon S3에 아래와 같이 파일을 업로드합니다. 

<img width="400" alt="noname" src="https://github.com/user-attachments/assets/42f530cf-11eb-456f-be5c-0ca58fe35fc7" />

[Knowledge Base Console](https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/knowledge-bases)에 접속해서 생성한 Knowledge Bases를 선택한 후에 아래와 같이 sync를 선택합니다. Sync가 완료가 되면 [Test Knowledge Base]를 선택하여 정상적으로 문서 정보를 가져오는지 확인합니다. 

<img width="600" alt="noname" src="https://github.com/user-attachments/assets/efd6aa45-2bc4-43b4-8fcb-d53252c09cce" />

## 배포하기

### EC2로 배포하기

AWS console의 EC2로 접속하여 [Launch an instance](https://us-west-2.console.aws.amazon.com/ec2/home?region=us-west-2#Instances:)를 선택합니다. [Launch instance]를 선택한 후에 적당한 Name을 입력합니다. (예: es) key pair은 "Proceed without key pair"을 선택하고 넘어갑니다. 

<img width="700" alt="ec2이름입력" src="https://github.com/user-attachments/assets/c551f4f3-186d-4256-8a7e-55b1a0a71a01" />


Instance가 준비되면 [Connet] - [EC2 Instance Connect]를 선택하여 아래처럼 접속합니다. 

<img width="700" alt="image" src="https://github.com/user-attachments/assets/e8a72859-4ac7-46af-b7ae-8546ea19e7a6" />

이후 아래와 같이 python, pip, git, boto3를 설치합니다.

```text
sudo yum install python3 python3-pip git docker -y
pip install boto3
```

Workshop의 경우에 아래 형태로 된 Credential을 복사하여 EC2 터미널에 입력합니다.

<img width="700" alt="credential" src="https://github.com/user-attachments/assets/261a24c4-8a02-46cb-892a-02fb4eec4551" />

아래와 같이 git source를 가져옵니다.

```python
git clone https://github.com/kyopark2014/es-us-project
```

아래와 같이 installer.py를 이용해 설치를 시작합니다.

```python
cd es-us-project && python3 installer.py
```

API 구현에 필요한 credential은 secret으로 관리합니다. 따라서 설치시 필요한 credential 입력이 필요한데 아래와 같은 방식을 활용하여 미리 credential을 준비합니다. 

- 일반 인터넷 검색: [Tavily Search](https://app.tavily.com/sign-in)에 접속하여 가입 후 API Key를 발급합니다. 이것은 tvly-로 시작합니다.  
- 날씨 검색: [openweathermap](https://home.openweathermap.org/api_keys)에 접속하여 API Key를 발급합니다. 이때 price plan은 "Free"를 선택합니다.

설치가 완료되면 아래와 같은 CloudFront로 접속하여 동작을 확인합니다. 

<img width="500" alt="cloudfront_address" src="https://github.com/user-attachments/assets/7ab1a699-eefb-4b55-b214-23cbeeeb7249" />

접속한 후 아래와 같이 Agent를 선택한 후에 적절한 MCP tool을 선택하여 원하는 작업을 수행합니다.

<img width="750" alt="image" src="https://github.com/user-attachments/assets/30ea945a-e896-438f-9f16-347f24c2f330" />

인프라가 더이상 필요없을 때에는 uninstaller.py를 이용해 제거합니다.

```text
python uninstaller.py
```


### 배포된 Application 업데이트 하기

AWS console의 EC2로 접속하여 [Launch an instance](https://us-west-2.console.aws.amazon.com/ec2/home?region=us-west-2#Instances:)를 선택하여 아래와 같이 아래와 같이 "app-for-es-us"라는 이름을 가지는 instance id를 선택합니다.

<img width="750" alt="image" src="https://github.com/user-attachments/assets/7d6d756a-03ba-4422-9413-9e4b6d3bc1da" />

[connect]를 선택한 후에 Session Manager를 선택하여 접속합니다. 

<img width="700" alt="image" src="https://github.com/user-attachments/assets/d1119cd6-08fb-4d3e-b1c2-77f2d7c1216a" />

이후 아래와 같이 업데이트한 후에 다시 브라우저에서 확인합니다.

```text
cd ~/es-us-project/ && sudo ./update.sh
```

### 실행 로그 확인

[EC2 console](https://us-west-2.console.aws.amazon.com/ec2/home?region=us-west-2#Instances:)에서 "app-for-es-us"라는 이름을 가지는 instance id를 선택 한 후에, EC2의 Session Manager를 이용해 접속합니다. 

먼저 아래와 같이 현재 docker container ID를 확인합니다.

```text
sudo docker ps
```

이후 아래와 같이 container ID를 이용해 로그를 확인합니다.

```text
sudo docker logs [container ID]
```

실제 실행시 결과는 아래와 같습니다.

<img width="600" src="https://github.com/user-attachments/assets/2ca72116-0077-48a0-94be-3ab15334e4dd" />

### Local에서 실행하기

AWS 환경을 잘 활용하기 위해서는 [AWS CLI를 설치](https://docs.aws.amazon.com/ko_kr/cli/v1/userguide/cli-chap-install.html)하여야 합니다. EC2에서 배포하는 경우에는 별도로 설치가 필요하지 않습니다. Local에 설치시는 아래 명령어를 참조합니다.

```text
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" 
unzip awscliv2.zip
sudo ./aws/install
```

AWS credential을 아래와 같이 AWS CLI를 이용해 등록합니다.

```text
aws configure
```

설치하다가 발생하는 각종 문제는 [Kiro-cli](https://aws.amazon.com/ko/blogs/korea/kiro-general-availability/)를 이용해 빠르게 수정합니다. 아래와 같이 설치할 수 있지만, Windows에서는 [Kiro 설치](https://kiro.dev/downloads/)에서 다운로드 설치합니다. 실행시는 셀에서 "kiro-cli"라고 입력합니다. 

```python
curl -fsSL https://cli.kiro.dev/install | bash
```

venv로 환경을 구성하면 편리하게 패키지를 관리합니다. 아래와 같이 환경을 설정합니다.

```text
python -m venv .venv
source .venv/bin/activate
```

이후 다운로드 받은 github 폴더로 이동한 후에 아래와 같이 필요한 패키지를 추가로 설치 합니다.

```text
pip install -r requirements.txt
```

이후 아래와 같은 명령어로 streamlit을 실행합니다. 

```text
streamlit run application/app.py
```

### 실행 결과

"Truck Gate의 Access Control에 대해 설명해주세요."라고 입력하면 아래와 같은 결과를 얻을 수 있습니다.

<img width="500" alt="image" src="https://github.com/user-attachments/assets/ffc54f04-30a7-46e8-9b44-ce3d07961eb4" />


"컨테이너 검사 과정을 시퀀스 다이어그램으로 보여줘"라고 입력하며 아래와 같은 diagram을 생성할 수 있습니다.

<img width="500" alt="image" src="./contents/77e8cb16.png" />


