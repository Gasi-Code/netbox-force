# NetBox Force — Guia (português)

[← Todos os idiomas](../README.md) · [README do projeto](../../README.md) · [Registo de alterações](../../CHANGELOG.md)

---

## 1. O que o plugin faz

O NetBox regista *o que* mudou. O NetBox Force decide *se a alteração é sequer
permitida*, e pode exigir uma justificação antes de a deixar passar.

Coloca-se entre cada operação de gravação ou eliminação e a base de dados. Antes
de escrever uma alteração pode verificar:

- se foi indicado um comentário de registo e se é suficientemente longo
- se o comentário não é composto apenas por palavras vazias
- se o comentário refere um número de bilhete
- se a alteração ocorre dentro de uma janela temporal aprovada
- se os valores dos campos seguem um padrão de nomes
- se os campos obrigatórios estão de facto preenchidos

Acompanham-no mais dois módulos:

- **Gestão de correções** — estado das correções, sistema operativo, responsáveis e
  histórico de atualizações por máquina virtual ou servidor físico, opcionalmente
  alimentado a partir do CheckMK.
- **Graylog** — envia eventos de auditoria para fora e traz informação de registo
  para junto do objeto a que pertence.

Tudo é opcional. Após a instalação apenas a verificação de presença do comentário
está ativa, com um mínimo de dois caracteres. O resto liga-se na interface web.

---

## 2. Requisitos

| Componente | Versão | Notas |
|---|---|---|
| NetBox | 4.0.0 ou posterior | |
| Python | 3.10 ou posterior | |
| PostgreSQL | — | Exigido pelo próprio NetBox |
| `cryptography` | qualquer | Vem com o NetBox. Sem ele, o segredo do CheckMK e o token do Graylog ficam guardados sem cifra, e o plugin di-lo na página de definições |
| `requests` | qualquer | Vem com o NetBox. Necessário para CheckMK e Graylog |
| Processo RQ | — | Apenas para a sincronização agendada do CheckMK e a recolha do Graylog. Sem ele, ambas continuam a funcionar a pedido, e a página di-lo |

---

## 3. Instalação

### 3.1 Instalar o pacote

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Registar o plugin

Em `configuration.py`:

```python
PLUGINS = ['netbox_force']
```

### 3.3 Executar as migrações

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 Reiniciar o NetBox

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <contentor> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <contentor> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <contentor>
```

Na imagem da LinuxServer.io **não** use scripts `custom-cont-init.d` para a
instalação. Correm *depois* dos scripts de arranque do NetBox, o que pode fazer
falhar as migrações. Os Docker Mods correm antes.

Uma instalação feita dentro do sistema de ficheiros do contentor não sobrevive a
uma atualização de imagem. Acrescente o plugin ao mecanismo persistente de
instalação de plugins da imagem, ou desaparecerá no próximo pull.

---

## 4. Atualização

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` é necessário porque o pip guarda em cache por
número de versão e, de outro modo, saltaria a reconstrução da mesma versão.

**Verifique antes de reiniciar.** Este passo importa o plugin sem tocar no processo
em execução. Se der erro, não reinicie: o NetBox em funcionamento ainda tem o
código anterior em memória e continua a trabalhar:

```bash
cd /opt/netbox/netbox
python manage.py check
```

Depois:

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Voltar atrás

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

Normalmente não é preciso reverter as migrações. As colunas adicionais não
incomodam o código mais antigo — ele simplesmente não as conhece. Ainda assim, faça
uma cópia da base de dados antes de atualizar.

---

## 5. Ficheiro de configuração

`PLUGINS_CONFIG` define **apenas os valores iniciais**. Após o primeiro arranque,
cada definição é gerida na interface web e guardada na base de dados.

```python
PLUGINS_CONFIG = {
    'netbox_force': {
        'min_length': 2,
        'exempt_users': ['automation', 'monitoring', 'netbox'],
        'enforce_on_create': False,
        'enforce_on_delete': True,
        'extra_exempt_models': [],
        'checkmk_secret': '',
    },
}
```

| Definição | Predefinição | Significado |
|---|---|---|
| `min_length` | `2` | Caracteres mínimos num comentário de registo |
| `exempt_users` | ver acima | Utilizadores isentos de todas as verificações, sem distinguir maiúsculas |
| `enforce_on_create` | `False` | Exigir comentário também ao criar |
| `enforce_on_delete` | `True` | Exigir comentário também ao eliminar |
| `extra_exempt_models` | `[]` | Mais modelos isentos, formato `app.model` |
| `checkmk_secret` | `''` | Opcional. Mantém o segredo do CheckMK totalmente fora da base de dados; passa então a ter precedência sobre o campo da interface |

---

## 6. As páginas

Os superutilizadores encontram **NetBox Force** na barra lateral. Todas as páginas
estão restritas a superutilizadores salvo indicação em contrário.

| Página | Finalidade |
|---|---|
| **Definições** | Todas as regras de imposição, isenções, módulos, webhook, CheckMK |
| **Regras de validação** | Padrões de nomes e campos obrigatórios, por modelo e campo |
| **Políticas por modelo** | Exceções às definições globais, por modelo |
| **Infrações** | Registo filtrável de cada alteração bloqueada, exportável em CSV |
| **Graylog** | Envio e leitura, ver secções 7 e 8 |
| **Painel** | Estatísticas: que funções estão ativas, alterações bloqueadas, utilizadores mais frequentes, tendência de 30 dias |
| **Modelos de importação** | Modelos CSV descarregáveis para a importação em massa do NetBox. Visíveis a todos os utilizadores autenticados quando ativados |
| **Guia** | Página de texto livre para os próprios utilizadores. Visível a todos os utilizadores autenticados quando ativada |
| **Gestão de correções** | Ver secção 9 |

Duas definições merecem menção à parte:

- **Interruptor global** — suspende todas as verificações, por exemplo durante uma
  janela de manutenção.
- **Modo de ensaio (dry-run)** — regista as infrações sem bloquear nada. É a forma
  correta de introduzir uma regra nova: vê-se o que *teria sido* bloqueado antes de
  travar alguém a sério.

---

## 7. Graylog — envio

Envia eventos de auditoria do NetBox para o Graylog através de GELF.

### Para quê

Três coisas não ficam registadas em mais lado nenhum do NetBox:

- **Inícios de sessão falhados.** O NetBox não os guarda de todo.
- **IP de origem e agente de utilizador** de uma alteração. O registo de alterações
  do NetBox não leva nenhum dos dois.
- **Alterações às definições do próprio plugin.** Não são cobertas pelo registo do
  NetBox — quem desligava a imposição não deixava antes qualquer rasto.

### Configuração

Na página **Graylog**, metade superior: anfitrião, porta, transporte. Depois
*Enviar evento de teste*.

Comece com **UDP**. Se não chegar nada, mude para **TCP**: por construção o UDP não
consegue comunicar uma falha, o TCP consegue. Isso distingue «porta errada» de
«mensagem descartada».

| Transporte | Confirma a entrega | Cifrado |
|---|---|---|
| UDP | não | não |
| TCP | sim | não |
| TCP + TLS | sim | sim |
| HTTP | sim | não |
| HTTPS | sim | sim |

O UDP está certo dentro de uma rede local e errado através da internet.

### O que é enviado

Uma linha por tipo de evento, cada uma com caixa e gravidade syslog: objeto criado,
alterado, eliminado; início de sessão; fim de sessão; início de sessão falhado;
alteração bloqueada; definições do plugin alteradas.

### Volume

Um pedido que altere mais objetos do que o limiar configurado é comunicado como
**um único evento de resumo**. Importar 500 equipamentos é uma operação: 500 linhas
quase idênticas tornam-na mais difícil de ver, não mais fácil.

Resumir em vez de estrangular o débito é uma escolha deliberada. Uma fila que se
esvazia mais devagar do que enche descarta os eventos *mais recentes*, ou seja,
precisamente a metade errada.

### Nomes dos campos

Todos os eventos levam os mesmos campos, para que as pesquisas continuem simples:

```
_app          netbox_force
_category     object_change | auth | violation | settings
_event        object_created, login_failed, …
_username
_client_ip
_user_agent
_object_type  dcim.device
_object_id
_object_name
_action       create | update | delete
_changed_fields
_request_id
_netbox_url
_outside_business_hours
```

`_request_id` agrupa tudo o que um pedido alterou. Quarenta equipamentos editados
de uma vez são uma operação, não quarenta enigmas.

### Três coisas a saber

- **Uma falha do Graylog não pode atrasar nem fazer falhar uma gravação no
  NetBox.** Os eventos entram numa fila limitada que um fio em segundo plano
  esvazia. Quando a fila enche, os novos eventos são descartados e contados, e o
  contador é mostrado na página.
- **O texto da mensagem é sempre em inglês**, seja qual for o idioma da interface.
  As consultas de alerta do Graylog assentam nesse texto; traduzi-lo quebraria em
  silêncio todos os alertas assim que alguém mudasse o idioma.
- **O IP do cliente é lido de `X-Forwarded-For`** quando presente. Esse cabeçalho
  vem do cliente e pode ser forjado se o NetBox estiver acessível sem um proxy
  inverso à frente.

---

## 8. Graylog — leitura

Traz informação do Graylog para o NetBox, de modo a avaliar um anfitrião sem abrir
um segundo separador.

### Configuração

Metade inferior da página **Graylog**: endereço web e token de API, depois *Testar
ligação*. O resultado indica a versão do Graylog, a forma de API de pesquisa
detetada, as origens mais ruidosas e os streams disponíveis. *Recolher agora*
executa uma recolha imediata.

**Emita o token para um utilizador do Graylog com perfil só de leitura.** É isso, e
não o código deste plugin, que garante que o Graylog não pode ser alterado a partir
do NetBox.

### O que «só de leitura» significa aqui, com precisão

Cada chamada obtém dados ou pede ao Graylog que execute uma pesquisa. O antigo
ponto de acesso de pesquisa é um `GET` simples. A mais recente API de pesquisa
Views não: exige um `POST` para registar uma pesquisa e outro para a executar. Isso
cria um objeto de pesquisa efémero dentro do Graylog e devolve resultados; os dados
guardados não são alterados. Se no seu ambiente só `GET` for aceitável, fixe a
forma de pesquisa em `legacy` nas definições.

### Associar origens a objetos do NetBox

Exato, por esta ordem, ganha a primeira correspondência:

| | Regra |
|---|---|
| 1 | **Associação manual** — uma vez definida, prevalece sempre |
| 2 | **Endereço IP** — a origem contra todos os IP do objeto |
| 3 | **Nome do anfitrião**, sem distinguir maiúsculas |
| 4 | **Nome do anfitrião após retirar um sufixo de domínio configurado** |

Tudo o resto fica sem associação e é listado como tal.

**Não existe, por opção deliberada, correspondência aproximada.** `srv-web-01` e
`srv-web-02` diferem num carácter, pelo que qualquer medida de semelhança lhes
chama 96 % de correspondência sendo duas máquinas distintas. Num esquema de nomes
numerado — isto é, em qualquer NetBox digno desse nome — o candidato mais parecido é
sistematicamente o errado. Os registos ficariam arquivados sob o servidor vizinho e
ninguém daria por isso. A semelhança serve apenas para **ordenar** as sugestões ao
lado de uma origem sem associação; nunca associa nada.

Se houver um relé syslog central à frente do Graylog, todas as mensagens levam o
endereço do relé e a regra 2 não acerta em nada útil. O campo de origem tem então
de levar o nome do anfitrião, e é para isso que servem as regras 3 e 4.

### As páginas

- **Origens** — tudo o que o Graylog reporta, com contadores, filtrável por
  associadas, sem associação, silenciosas, nunca vistas e ignoradas.
- **Silenciosas** — associadas no NetBox mas sem enviar nada. Mortas, mal
  configuradas, ou um resto. Nenhum dos sistemas deteta isto sozinho.
- **Nunca vistas no Graylog** — a outra metade da verificação cruzada.
- **Cluster** — nós com semáforo verde/amarelo/vermelho, saúde do indexador, atraso
  do diário, cada nó ligado à sua máquina virtual no NetBox.
- **No objeto** — os equipamentos e máquinas virtuais com origem associada recebem
  um painel Graylog com contadores, mensagens recentes a pedido e uma ligação para
  o Graylog.

### Carga e segurança

- Uma recolha é **uma única consulta agrupada para todos os anfitriões**, não uma
  consulta por equipamento. Um local com 800 equipamentos custa três pedidos.
- O painel do cluster e a lista de mensagens carregam **depois** de a página ser
  desenhada. Um Graylog lento ou morto dá um painel vazio, nunca uma página do
  NetBox bloqueada.
- A associação vive na tabela do próprio plugin. **O Graylog nunca escreve num
  objeto central do NetBox** — remover o plugin remove a associação e deixa o NetBox
  intacto.
- O ponto de acesso das mensagens só responde para uma origem associada a um objeto
  que quem chama tenha permissão para ver.

---

## 9. Gestão de correções e CheckMK

Acompanha o estado das correções, o sistema operativo, os responsáveis e o
histórico de atualizações por máquina virtual ou servidor físico.

- **Estado** verde / amarelo / vermelho, mantido à mão ou lido do CheckMK.
- **Limiar de atraso** — as entradas sem correção em N dias são marcadas como
  atrasadas.
- **Escalada** — uma entrada que fique N dias em *amarelo* passa sozinha a
  *vermelho*.
- **Contactos** — administrador e responsável de processo a partir dos objetos de
  contacto do NetBox.
- **Histórico de atualizações** — uma entrada por passagem de correções, com número
  de bilhete e nota.
- **O acesso** é concedido por nome de grupo do NetBox nas definições do plugin, não
  através das permissões do Django.

### CheckMK

A integração é um **pull**: o NetBox lê do CheckMK. Nada é escrito no CheckMK, pelo
que basta um utilizador de automação só de leitura.

Configura-se na página de definições: URL do sítio, utilizador de automação,
segredo, filtro de serviços e intervalo de sincronização. O segredo é guardado
cifrado e nunca mais é mostrado.

Uma sincronização parada é a falha que mais dói, porque a página continua a mostrar
um estado de correções que deixou de ser verdade em silêncio. O painel diz por isso
abertamente quando a última sincronização bem-sucedida é mais antiga do que o dobro
do intervalo configurado.

---

## 10. Resolução de problemas

**O plugin não aparece na barra lateral.**
`PLUGINS` está em `configuration.py`? As migrações foram executadas? O NetBox foi
reiniciado? As etiquetas da barra lateral só se atualizam no reinício; os
separadores dentro do plugin, de imediato.

**As alterações não são bloqueadas.**
Verifique, por esta ordem: o interruptor global, o modo de ensaio, se o utilizador
consta dos utilizadores ou grupos isentos, e se uma política por modelo desliga a
imposição para esse modelo.

**Uma página indica uma coluna em falta.**
As migrações não foram executadas, ou só em parte.
`python manage.py migrate netbox_force`.

**«Não há nenhum processo em segundo plano a correr.»**
O `netbox-rq` não está a correr. A sincronização do CheckMK e a recolha do Graylog
só correm ao carregar no botão.

**Não chega nada ao Graylog.**
Mude o transporte de UDP para TCP. O UDP não consegue comunicar uma falha; o TCP
consegue, e a sua mensagem de erro diz se a porta está errada ou se a mensagem foi
recusada.

**O painel do Graylog num equipamento fica vazio.**
O equipamento não tem origem associada. Abra *Origens → Sem associação* e associe-a,
ou acrescente o seu sufixo de domínio nas definições para que o FQDN possa ser
encurtado.

**Depois de mudar `SECRET_KEY`, o segredo do CheckMK ou o token do Graylog deixa de funcionar.**
Ambos estão cifrados com uma chave derivada de `SECRET_KEY`. Têm de ser
introduzidos de novo.

---

## 11. Mudar de idioma

O idioma é uma definição **por instalação**, não por utilizador. Muda-se na página
de definições.

Os separadores e páginas dentro do plugin mudam de imediato. As etiquetas da barra
lateral são construídas uma só vez no arranque e só mudam após reiniciar o NetBox.

As mensagens mostradas aos utilizadores ao bloquear seguem esta definição. As
mensagens de erro da API e as enviadas ao Graylog mantêm-se em inglês — ver a nota
no [índice da documentação](../README.md).

---

## 12. Licença

AGPL-3.0. Ver [LICENSE](../../LICENSE).
