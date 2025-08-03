# Hyun Project

여기서는 Streamlit 이용한 간단한 UI와 Knowledge Base를 이용한 RAG를 이용하여 strands agent 기반의 chatbot을 구현합니다. 

## RAG 구현

[Knowledge Base](https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/knowledge-bases)에 접속해서 [Create]를 선택하여 RAG를 생성합니다. 완료가 되면 Knowledge Base의 ID를 확인합니다.

Amazon S3에 아래와 같이 파일을 업로드합니다. 

<img width="525" height="380" alt="noname" src="https://github.com/user-attachments/assets/42f530cf-11eb-456f-be5c-0ca58fe35fc7" />



## Strands Agent의 활용

Strands agent는 multi step reasoning을 통해 향상된 RAG 검색을 가능하게 해줍니다.



