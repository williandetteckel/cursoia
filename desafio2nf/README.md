# NOTAVIA

### Necessita de uma chave OPENAI_API_KEY

Criar um arquivo .env na raiz do projeto e colocar a chave OPENAI_API_KEY.

Esta solução utiliza o modelo gpt-4o-mini que possui um custo muito baixo (mais baixo do que versões anteriores como gpt-3.5x).

Não está sendo passado aqui o arquivo ZIP de notas fiscais. 

Para executar, esteja com o prompt do terminal no diretório raiz do projeto e digite:

streamlit run app.py

COMPORTAMENTO ESTRANHO sabido do Streamlit na interface (a ser resolvido em próxima versão): Depois de fazer a primeira pergunta, clicar no botão Perguntar e exibir a primeira resposta, retornar à caixa de Pergunta e digitar uma nova pergunta é a coisa mais óbvia a ser feita, porém, para que NÃO REPITA a execução da pergunta anterior, faça qualquer alteração na pergunta apresentada e clique abaixo da caixa de texto da pergunta na área em branco da tela. A resposta anterior irá ser limpa e, AGORA SIM, pode entrar com uma nova pergunta e clicar no botão Perguntar que o processo ocorrerá normalmente. Isso deve ser feito a cada nova pergunta por enquanto.

