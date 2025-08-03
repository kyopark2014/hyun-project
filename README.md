# Hyun Project

여기서는 Streamlit 이용한 간단한 UI와 Knowledge Base를 이용한 RAG를 이용하여 strands agent 기반의 chatbot을 구현합니다. 전체적인 architecture는 아래와 같습니다. MCP server로 Knowledge Base, Code Interpreter를 이용하고 strands agent를 이용해 관련된 문서를 조회하여 답변을 구하고 필요하다면 다이어그램을 그래서 이해를 돕습니다.

<img width="500" height="420" alt="image" src="https://github.com/user-attachments/assets/4d666a04-f100-45c8-8d18-3e84fdc93cf8" />

## RAG 구현

[Knowledge Base](https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/knowledge-bases)에 접속해서 [Create]를 선택하여 RAG를 생성합니다. 완료가 되면 Knowledge Base의 ID를 확인합니다.

Amazon S3에 아래와 같이 파일을 업로드합니다. 

<img width="400" alt="noname" src="https://github.com/user-attachments/assets/42f530cf-11eb-456f-be5c-0ca58fe35fc7" />

[Knowledge Base Console](https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/knowledge-bases)에 접속해서 생성한 Knowledge Bases를 선택한 후에 아래와 같이 sync를 선택합니다. Sync가 완료가 되면 [Test Knowledge Base]를 선택하여 정상적으로 문서 정보를 가져오는지 확인합니다. 

<img width="600" alt="noname" src="https://github.com/user-attachments/assets/efd6aa45-2bc4-43b4-8fcb-d53252c09cce" />

## Strands Agent의 활용

Strands agent는 multi-step reasoning을 통해 향상된 RAG 검색을 가능하게 해줍니다. 이를 활용하기 위해 먼저 아래와 같이 git으로 부터 소스를 가져옵니다.

```text
git clone https://github.com/kyopark2014/hyun-project
```

"application" 폴더의 [config.json](./application/config.json)을 선택한 후에 아래와 같이 knowledge_base_id를 업데이트 합니다. knowledge_base_id은 생성한 Knowledge Base의 ID입니다.

```java
{
    "projectName":"hyun-project",
    "region":"us-west-2",
    "knowledge_base_id":"O2IGZXMQXO"
 }
```

이제 필요한 패키지를 설치합니다.

```text
pip install -r requirements.txt
```

이후 아래와 같이 streamlit을 실행합니다.

```text
streamlit run application/app.py
```

죄측의 메뉴에서 사용하는 모델을 선택할 수 있으며, "Debug Mode"로 최종 결과와 전체 결과를 구분하여 확인할 수 있습니다. 

## 실행 결과

"Truck Gate의 Access Control에 대해 설명해주세요."라고 입력하면 아래와 같은 결과를 얻을 수 있습니다.

<img width="500" alt="image" src="https://github.com/user-attachments/assets/ffc54f04-30a7-46e8-9b44-ce3d07961eb4" />


"컨테이너 검사 과정을 시퀀스 다이어그램으로 보여줘"라고 입력하며 아래와 같은 diagram을 생성할 수 있습니다.

<img width="500" alt="image" src="./contents/77e8cb16.png" />


